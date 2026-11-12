"use client";

import React, { useState, useEffect } from "react";

const API_BASE = "";

export default function Home() {
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [dashboardOpen, setDashboardOpen] = useState(false);
  const [mcpStatusText, setMcpStatusText] = useState("MCP Connecting...");
  const [orders, setOrders] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);

  // Explain modal state
  const [explainModalOpen, setExplainModalOpen] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState(null);
  const [aiSummary, setAiSummary] = useState(
    "Generating compact AI explanation via TRUSTMATE MCP explain_score...",
  );

  // Risk modal state
  const [riskModalOpen, setRiskModalOpen] = useState(false);
  const [pendingRiskOffer, setPendingRiskOffer] = useState(null);

  // Initialize status & window message listener
  useEffect(() => {
    async function fetchStatus() {
      try {
        const res = await fetch(`${API_BASE}/api/status`);
        const data = await res.json();
        setMcpStatusText(
          "TRUSTMATE: " +
            (data.trust_mcp_url?.includes("8001") ? "Mock Mode" : "Live MCP"),
        );
      } catch {
        setMcpStatusText("TRUSTMATE: Connected");
      }
    }
    fetchStatus();

    const handleMessage = (event) => {
      if (event.data && event.data.type === "PAYPAL_ORDER_CAPTURED") {
        alert(
          `✅ Payment Completed Successfully via PayPal Sandbox!\nOrder ID: ${event.data.order_id}`,
        );
        loadDashboard();
      }
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const handleSearch = async (overrideQuery) => {
    const q = (
      overrideQuery !== undefined ? overrideQuery : searchInput
    ).trim();
    if (!q) return;

    setLoading(true);
    setResults(null);
    setDashboardOpen(false);

    try {
      const res = await fetch(`${API_BASE}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });
      const data = await res.json();
      setLoading(false);

      if (!data.success && data.error) {
        alert(data.error);
        return;
      }
      setResults(data);
    } catch (err) {
      setLoading(false);
      alert("Search failed: " + err.message);
    }
  };

  const setQueryAndSearch = (q) => {
    setSearchInput(q);
    handleSearch(q);
  };

  const openExplainModal = async (offer) => {
    setSelectedOffer(offer);
    setAiSummary(
      "Generating compact AI explanation via TRUSTMATE MCP explain_score...",
    );
    setExplainModalOpen(true);

    try {
      const res = await fetch(`${API_BASE}/api/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seller: offer.seller, url: offer.url }),
      });
      const data = await res.json();
      setAiSummary(data.summary || "No explanation summary available.");
    } catch (e) {
      setAiSummary("Could not load AI explanation: " + e.message);
    }
  };

  const closeExplainModal = () => {
    setExplainModalOpen(false);
    setSelectedOffer(null);
  };

  const startCheckout = (offer) => {
    // High-Risk gating check
    if (offer.trust && offer.trust.score !== null && offer.trust.score < 2.5) {
      setPendingRiskOffer(offer);
      setRiskModalOpen(true);
      return;
    }
    executeOrderCreation(offer, false);
  };

  const confirmRiskPayment = () => {
    setRiskModalOpen(false);
    if (pendingRiskOffer) {
      executeOrderCreation(pendingRiskOffer, true);
    }
  };

  const closeRiskModal = () => {
    setRiskModalOpen(false);
    setPendingRiskOffer(null);
  };

  const executeOrderCreation = async (offer, riskConfirmed) => {
    try {
      const res = await fetch(`${API_BASE}/api/order/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_title: offer.title,
          seller_name: offer.seller,
          price_inr: offer.price_inr,
          trust_score: offer.trust ? offer.trust.score : null,
          trust_label: offer.trust ? offer.trust.label : "Unrated",
          risk_confirmed: riskConfirmed,
        }),
      });

      const data = await res.json();
      if (data.error) {
        alert("Order creation failed: " + data.message);
        return;
      }

      // Open PayPal approval popup
      const width = 500,
        height = 650;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      const approveUrl = data.approve_url?.startsWith("http")
        ? data.approve_url
        : `${API_BASE}${data.approve_url}`;
      window.open(
        approveUrl,
        "PayPalApproval",
        `width=${width},height=${height},top=${top},left=${left}`,
      );
    } catch (e) {
      alert("Failed to initiate PayPal order: " + e.message);
    }
  };

  const toggleDashboard = async () => {
    const nextState = !dashboardOpen;
    setDashboardOpen(nextState);
    if (nextState) {
      await loadDashboard();
    }
  };

  const loadDashboard = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard`);
      const data = await res.json();
      setOrders(data.orders || []);
      setRecentSearches(data.recent_searches || []);
    } catch {}
  };

  const renderBadge = (trust) => {
    if (!trust || trust.score === null) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300">
          <i className="fa-solid fa-circle-question text-slate-400"></i>
          <span>Unrated</span>
        </span>
      );
    }
    const score = trust.score.toFixed(1);
    if (trust.score >= 4.0) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-xs">
          <i className="fa-solid fa-shield-check text-emerald-600"></i>
          <span>
            {score} • {trust.label}
          </span>
        </span>
      );
    } else if (trust.score >= 2.5) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
          <i className="fa-solid fa-triangle-exclamation text-amber-600"></i>
          <span>
            {score} • {trust.label}
          </span>
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 animate-pulse">
          <i className="fa-solid fa-shield-xmark text-rose-600"></i>
          <span>{score} • Risky</span>
        </span>
      );
    }
  };

  return (
    <>
      {/* Top Header Navigation */}
      <header className="glass sticky top-0 z-30 border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 h-full">
            <div className=" h-full flex items-center space-x-1  ">
              <div className="image  flex items-center">
                <img
                  src="https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0e/PayPal_2024_%28Icon%29.svg/250px-PayPal_2024_%28Icon%29.svg.png?utm_source=en.wikipedia.org&utm_campaign=parser&utm_content=thumbnail"
                  className="w-12 h-12 "
                  alt=""
                />
              </div>
              <div className="heading flex flex-col">
                <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-[#002990]  to-[#0089FA] bg-clip-text text-transparent flex items-center h-full ">
                  TRUSTMATE
                </span>
                <span className="text-xs font-medium  h-[70%] flex items-end ">
                  Services
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 text-xs px-3 py-1.5 rounded-[5px] bg-slate-100 text-black-600 border border-slate-200">
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-[5px] bg-blue-50 text-black-700 border ">
                PayPal AI Agent
              </span>
            </div>
            <button
              onClick={toggleDashboard}
              className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-[5px] bg-white border border-slate-200 hover:bg-slate-50 transition shadow-xs"
            >
              <i className="fa-solid fa-clock-rotate-left text-slate-500"></i>
              <span>Audit Dashboard</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero Section */}
        <div className="text-center max-w-4xl mx-auto space-y-4 pt-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1   text-sm font-semibold text-black-700">
            <i className="fa-solid fa-scale-balanced"></i>
            <span className="font-medium">Trust comes first, price second</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extralight text-black-900 tracking-tight leading-tight">
            Never get scammed by a{" "}
            <span>
              &quot;<span className="font-semibold">Too Good</span>&quot;
            </span>{" "}
            deal again.
          </h1>
          <p className="text-sm text-black-600 max-w-2xl mx-auto">
            TRUSTMATE scores seller authenticity via Places, domain history, and
            Safe Browsing. We gate untrusted sellers before you pay with PayPal.
          </p>

          {/* Search Input Box */}
          <div className="pt-2">
            <div className="relative max-w-2xl mx-auto">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
                <i className="fa-solid fa-magnifying-glass text-lg"></i>
              </div>
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="e.g. laptop under 60000 for programming"
                className="w-full pl-12 pr-32 py-4 rounded-[5px] bg-white border-2 border-slate-200 focus:border-blue-600 focus:outline-none focus:ring-4 focus:ring-blue-100 text-slate-800 text-base shadow-lg shadow-slate-200/50 transition"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
              />
              <div className="absolute inset-y-2 right-2 flex items-center">
                <button
                  onClick={() => handleSearch()}
                  className="h-full px-5 bg-gradient-to-r from-[#0089FA] to-[#002990]  hover:bg-white hover:bg-clip-text hover:text-transparent text-white font-semibold rounded-[5px] transition shadow-md flex items-center space-x-2"
                >
                  <span>Inspect</span>
                  <i className="fa-solid fa-arrow-right text-xs"></i>
                </button>
              </div>
            </div>

            {/* Prompt Suggestion Chips */}
            <div className="flex flex-wrap items-center justify-center gap-2 pt-3 text-xs text-black-500">
              <span className="font-medium">Try:</span>
              <button
                onClick={() =>
                  setQueryAndSearch("laptop under 60000 for programming")
                }
                className="px-2.5 py-1 rounded-[10px] bg-slate-100 hover:bg-slate-200 text-black-700 transition"
              >
                💻 Laptop under ₹60,000 for programming
              </button>
              <button
                onClick={() =>
                  setQueryAndSearch("noise cancelling headphones under 15000")
                }
                className="px-2.5 py-1 rounded-[10px] bg-slate-100 hover:bg-slate-200 text-black-700 transition"
              >
                🎧 Headphones under ₹15,000
              </button>
              <button
                onClick={() =>
                  setQueryAndSearch("mechanical keyboard under 4000")
                }
                className="px-2.5 py-1 rounded-[10px] bg-slate-100 hover:bg-slate-200 text-black-700 transition"
              >
                ⌨️ Keyboard under ₹4,000
              </button>
            </div>
          </div>
        </div>

        {/* Loading Indicator */}
        {loading && (
          <div className="text-center py-12 space-y-4">
            <div
              className="inline-block h-10 w-10 animate-spin rounded-full bg-[conic-gradient(from_0deg,transparent_25%,#0089FA_75%,#002990_100%)] [mask-image:radial-gradient(farthest-side,transparent_calc(100%-4px),#000_calc(100%-4px))]"
              role="status"
              aria-label="loading"
            />

            <p className="text-sm font-semibold text-slate-700">
              Agent executing{" "}
              <code className="text-xs bg-gradient-to-r from-[#0089FA] to-[#002990] bg-clip-text text-transparent px-2 py-1 rounded ">
                rank_offers
              </code>{" "}
              tool on TRUSTMATE MCP...
            </p>
            <p className="text-xs text-black-400">
              Verifying domain age, HTTPS certificates, Places listings &amp;
              Safe Browsing
            </p>
          </div>
        )}

        {/* Search Results Section */}
        {!loading && results && !dashboardOpen && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-200 text-sm">
              <div>
                <h2 className="text-2xl font-medium text-slate-900">
                  Verified Offers for &quot;
                  <span className="font-bold">{results.query}</span>&quot;
                </h2>
                <p className="text-xs text-black-500">
                  Ranked trust-first. Sellers below 2.5 are gated.
                </p>
              </div>
              <div className="mt-2 sm:mt-0 flex items-center space-x-2 text-xs font-semibold text-slate-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs">
                <i className="fa-solid fa-arrow-down-wide-short text-blue-600"></i>
                <span>Sort: 70% Trust + 30% Price</span>
              </div>
            </div>

            {/* Verification Notice */}
            {results.unverified_notes?.length > 0 && (
              <section
                role="status"
                aria-label="Verification notice"
                className="relative overflow-hidden rounded-xl border border-[#D5E5F7] bg-white shadow-[0_2px_8px_rgba(0,48,135,0.04)]"
              >
                {/* PayPal blue accent */}
                <div className="absolute left-0 top-0 h-full w-[3px] bg-[#0070E0]" />

                <div className="flex items-start gap-3 px-4 py-3.5 sm:px-5">
                  {/* Icon */}

                  {/* Content */}
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-[13px] font-semibold tracking-tight text-black">
                        Verification Notice
                      </h3>

                      <span className="inline-flex items-center rounded-[5px] border border-[#D5E5F7] bg-[#F5F9FF] px-2 py-0.5 text-[10px] font-medium text-black">
                        Evidence transparency
                      </span>
                    </div>

                    <p className="mt-1 text-xs leading-[1.65] text-black-600">
                      Some offers passed standard ranking eligibility but did
                      not meet the evidence requirements for an automatic
                      recommendation.
                    </p>

                    {/* Details */}
                    <ul className="mt-2.5 space-y-2">
                      {results.unverified_notes.map((note, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-xs leading-relaxed text-black-600"
                        >
                          <span className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full bg-[#0070E0]" />
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            )}

            {/* Offers Grid */}
            {results.offers.length === 0 ? (
              <div className="bg-white rounded-3xl border border-slate-200 p-12 text-center space-y-3 shadow-xs">
                <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto text-xl">
                  <i className="fa-solid fa-box-open"></i>
                </div>
                <h3 className="text-base font-bold text-slate-800">
                  No Eligible Offers Found
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  No verified offers matched your query within the specified
                  budget. Try adjusting your search keywords or increasing your
                  budget limit.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-200 border-y border-slate-200 bg-white">
                {results.offers.map((offer, idx) => {
                  const priceUsd = (offer.price_inr * 0.012).toFixed(2);

                  return (
                    <article
                      key={offer.id || idx}
                      className={`relative py-6 sm:py-7 pl-4 sm:pl-6 pr-2 sm:pr-4 transition-colors hover:bg-slate-50/60 ${
                        offer.recommended
                          ? "border-l-[3px] border-l-[#0070E0]"
                          : "border-l-[3px] border-l-transparent"
                      }`}
                    >
                      {/* Product heading */}
                      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          {offer.recommended && (
                            <div className="flex items-center gap-1.5 mb-2">
                              <i className="fa-solid fa-circle-check text-[#0070E0] text-xs" />
                              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#0070E0]">
                                Recommended pick · Trust-first
                              </span>
                            </div>
                          )}

                          <h3 className="text-[15px] sm:text-base font-medium text-[#071B36] leading-snug">
                            {offer.title}
                          </h3>

                          <p className="mt-1 text-xs font-light text-black-500">
                            Sold by{" "}
                            <span className="font-bold text-black-700">
                              {offer.seller}
                            </span>
                          </p>
                        </div>

                        {/* Trust score */}
                        <button
                          type="button"
                          onClick={() => openExplainModal(offer)}
                          className="self-start shrink-0 hover:opacity-75 transition"
                          aria-label="Inspect trust score"
                        >
                          {renderBadge(offer.trust)}
                        </button>
                      </div>

                      {/* Trade-off explanation - no alert box */}
                      {offer.tradeoff_note && (
                        <div className="mt-4 flex items-start gap-2.5 max-w-4xl">
                          <i className="fa-solid fa-circle-info text-[#B7791F] text-xs mt-[3px] shrink-0" />

                          <div className="min-w-0">
                            <p className="text-xs leading-[1.7] text-black-600">
                              <span className="font-semibold text-[#8A5A16]">
                                Recommendation restricted:{" "}
                              </span>
                              {offer.tradeoff_note}
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Price and inspection */}
                      <div className="mt-5 pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
                        <div>
                          <p className="text-[10px] font-bold uppercase tracking-wider text-black-400 mb-1">
                            Offer price
                          </p>

                          <div className="text-[27px] sm:text-3xl font-bold tracking-tight text-[#071B36]">
                            ₹
                            {Math.round(offer.price_inr).toLocaleString(
                              "en-IN",
                            )}
                          </div>

                          <p className="mt-0.5 text-xs text-black-400">
                            ≈ ${priceUsd} USD
                            <span className="mx-1">·</span>
                            PayPal Sandbox
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() => openExplainModal(offer)}
                          className="group inline-flex items-center gap-2 self-start sm:self-auto text-xs font-semibold text-black hover:text-[#003087] transition-colors"
                        >
                          Inspect evidence & signals
                          <i className="fa-solid fa-arrow-right text-[10px] transition-transform group-hover:translate-x-1" />
                        </button>
                      </div>

                      {/* Checkout */}
                      <div className="mt-5 flex justify-end">
                        <button
                          type="button"
                          onClick={() => startCheckout(offer)}
                          className="w-full sm:w-auto min-w-[230px] bg-[#003087] hover:bg-[#0047AB] active:bg-[#00246A] text-white py-3 px-6 rounded-lg text-xs font-semibold transition-colors duration-200 flex items-center justify-center gap-2"
                        >
                          <i className="fa-brands fa-paypal text-base text-[#00A8E0]" />
                          <span className="font-medium">
                            Approve & Pay with PayPal
                          </span>
                          <i className="fa-solid fa-arrow-right text-[10px] opacity-70" />
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Dashboard Section */}

        {dashboardOpen && (
          <div className="space-y-7 pt-4">
            {/* Dashboard Header */}
            <div
              className="flex flex-col sm:flex-row sm:items-center
      justify-between gap-4 pb-5 border-b border-slate-200"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-1.5 h-6 bg-[#0070E0] rounded-full"></span>
                  <h2 className="text-2xl font-bold tracking-tight text-[#071B36]">
                    Purchase &amp; Trust Audit
                  </h2>
                </div>

                <p className="text-xs text-slate-500 ml-3.5">
                  Transaction history, seller verification and search activity.
                </p>
              </div>

              <button
                onClick={toggleDashboard}
                className="inline-flex items-center gap-2 text-xs
        font-semibold text-[#0070E0] hover:text-[#003087]
        transition-colors"
              >
                <i className="fa-solid fa-arrow-left text-[10px]"></i>
                Back to Search
              </button>
            </div>

            {/* Overview Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Total Orders */}
              <div
                className="bg-white border border-slate-200
        rounded-xl px-5 py-4"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500">
                    Total PayPal Orders
                  </span>
                  <i className="fa-brands fa-paypal text-[#0070E0] text-lg"></i>
                </div>

                <p className="text-2xl font-bold text-[#071B36] mt-3">
                  {orders.length}
                </p>

                
              </div>

              {/* Captured Orders */}
              <div
                className="bg-white border border-slate-200
        rounded-xl px-5 py-4"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500">
                    Completed Transactions
                  </span>
                  <i
                    className="fa-solid fa-circle-check
            text-emerald-600 text-base"
                  ></i>
                </div>

                <p className="text-2xl font-bold text-[#071B36] mt-3">
                  {orders.filter((o) => o.status === "COMPLETED").length}
                </p>

                
              </div>

              {/* Trust Checks */}
              <div
                className="bg-white border border-slate-200
        rounded-xl px-5 py-4"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500">
                    Total Trust Checks
                  </span>
                  <i
                    className="fa-solid fa-shield-halved
            text-[#0070E0] text-base"
                  ></i>
                </div>

                <p className="text-2xl font-bold text-[#071B36] mt-3">
                  {recentSearches.length}
                </p>

                
              </div>
            </div>

            {/* Dashboard Data */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* PayPal Transactions */}
              <section
                className="bg-white border border-slate-200
        rounded-xl overflow-hidden"
              >
                <div
                  className="px-5 py-4 border-b border-slate-100
          flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3">
                    

                    <div>
                      <h3 className="text-sm font-bold text-[#071B36]">
                        PayPal Transactions
                      </h3>
                      
                    </div>
                  </div>

                  <span
                    className="text-[11px] font-semibold
            text-[#003087] bg-[#EAF4FF] px-2.5 py-1 rounded-md"
                  >
                    {orders.length} Orders
                  </span>
                </div>

                <div className="max-h-[460px] overflow-y-auto">
                  {orders.length === 0 ? (
                    <div
                      className="min-h-[280px] flex flex-col
              items-center justify-center text-center px-6"
                    >
                      <div
                        className="w-12 h-12 rounded-full
                bg-slate-50 flex items-center justify-center"
                      >
                        <i
                          className="fa-solid fa-receipt
                  text-slate-300 text-xl"
                        ></i>
                      </div>

                      <h4
                        className="text-sm font-semibold
                text-slate-700 mt-4"
                      >
                        No transactions yet
                      </h4>

                      
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {orders.map((o) => (
                        <div
                          key={o.id}
                          className="px-5 py-4 hover:bg-slate-50/70
                  transition-colors"
                        >
                          {/* Product and amount */}
                          <div
                            className="flex items-start
                    justify-between gap-3"
                          >
                            <div className="min-w-0">
                              <h4
                                className="text-[13px] font-semibold
                        text-[#071B36] truncate"
                              >
                                {o.item_title}
                              </h4>

                              <p className="text-xs text-slate-500 mt-1">
                                {o.seller_name}
                              </p>
                            </div>

                            <p
                              className="text-sm font-bold
                      text-[#071B36] whitespace-nowrap"
                            >
                              ${Number(o.amount_usd || 0).toFixed(2)}
                            </p>
                          </div>

                          {/* Transaction details */}
                          <div
                            className="flex flex-wrap items-center
                    justify-between gap-2 mt-3"
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={`inline-flex items-center
                        gap-1.5 text-[10px] font-semibold
                        px-2 py-1 rounded-md ${
                          o.status === "COMPLETED"
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-amber-50 text-amber-700"
                        }`}
                              >
                                <span
                                  className={`w-1.5 h-1.5 rounded-full ${
                                    o.status === "COMPLETED"
                                      ? "bg-emerald-500"
                                      : "bg-amber-500"
                                  }`}
                                ></span>

                                {o.status === "COMPLETED"
                                  ? "Captured"
                                  : o.status === "CREATED"
                                    ? "Created"
                                    : o.status}
                              </span>

                              <span
                                className="text-[10px]
                        text-slate-400"
                              >
                                Trust:{" "}
                                {o.trust_score !== null &&
                                o.trust_score !== undefined
                                  ? o.trust_score.toFixed(1)
                                  : "Unrated"}
                              </span>
                            </div>

                            <span
                              title={o.order_id}
                              className="text-[10px] font-mono
                      text-slate-400 truncate max-w-[145px]"
                            >
                              {o.order_id}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </section>

              {/* Recent Trust Checks */}
              <section
                className="bg-white border border-slate-200
        rounded-xl overflow-hidden"
              >
                <div
                  className="px-5 py-4 border-b border-slate-100
          flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3">
                    

                    <div>
                      <h3 className="text-sm font-bold text-[#071B36]">
                        Recent Trust Checks
                      </h3>
                      
                    </div>
                  </div>

                  <span
                    className="text-[11px] font-semibold
            text-[#003087] bg-[#EAF4FF] px-2.5 py-1 rounded-md"
                  >
                    {recentSearches.length} Searches
                  </span>
                </div>

                <div className="max-h-[460px] overflow-y-auto">
                  {recentSearches.length === 0 ? (
                    <div
                      className="min-h-[280px] flex flex-col
              items-center justify-center text-center px-6"
                    >
                      <div
                        className="w-12 h-12 rounded-full
                bg-slate-50 flex items-center justify-center"
                      >
                        <i
                          className="fa-solid fa-magnifying-glass
                  text-slate-300 text-lg"
                        ></i>
                      </div>

                      <h4
                        className="text-sm font-semibold
                text-slate-700 mt-4"
                      >
                        No trust checks recorded
                      </h4>

                      
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {recentSearches.map((s) => (
                        <div
                          key={s.id}
                          className="px-5 py-4 hover:bg-slate-50/70
                  transition-colors"
                        >
                          <div
                            className="flex items-start
                    justify-between gap-3"
                          >
                            <div className="min-w-0 flex-1">
                              <h4
                                className="text-[13px] font-semibold
                        text-[#071B36] break-words"
                              >
                                {s.query}
                              </h4>

                              <p className="text-[11px] text-slate-400 mt-1">
                                <i className="fa-regular fa-clock mr-1"></i>
                                {s.created_at
                                  ? new Date(s.created_at).toLocaleString(
                                      "en-IN",
                                      {
                                        day: "2-digit",
                                        month: "short",
                                        year: "numeric",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                      },
                                    )
                                  : "Date unavailable"}
                              </p>
                            </div>

                            <div className="shrink-0 text-right">
                              <p
                                className="text-[10px] uppercase
                        tracking-wide text-slate-400"
                              >
                                Budget
                              </p>

                              <p
                                className="text-xs font-bold
                        text-[#003087] mt-1 whitespace-nowrap"
                              >
                                ₹
                                {Number(s.budget_inr || 0).toLocaleString(
                                  "en-IN",
                                )}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </section>
            </div>
          </div>
        )}
      </main>

      {/* Tap-To-Explain Factors Modal */}
      {explainModalOpen && selectedOffer && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center
    p-3 sm:p-5 bg-[#071B36]/60 backdrop-blur-sm"
          onClick={closeExplainModal}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-[5px] max-w-2xl w-full
      max-h-[90vh] flex flex-col overflow-hidden
      shadow-2xl border border-slate-200"
          >
            {/* Header */}
            <div
              className="px-5 sm:px-7 py-5 flex items-center
        justify-between border-b border-slate-100 shrink-0"
            >
              <div className="min-w-0">
                <h3
                  className="text-lg font-bold text-[#071B36]
            flex items-center flex-wrap gap-2"
                >
                  <span>{selectedOffer.seller}</span>
                  {renderBadge(selectedOffer.trust)}
                </h3>

                <p className="text-xs text-black-400 mt-1">
                  Tap-to-Explain Signal Breakdown
                </p>
              </div>

              <button
                onClick={closeExplainModal}
                className="w-9 h-9 shrink-0 rounded-full
           hover:bg-[#0089FA] hover:text-[#002990]
          text-slate-500 flex items-center justify-center transition"
              >
                <i className="fa-solid fa-xmark"></i>
              </button>
            </div>

            {/* Content */}
            <div
              className="flex-1 min-h-0 overflow-y-auto
        px-5 sm:px-7 py-6 space-y-7"
            >
              {/* AI Summary */}

              {/* AI Summary */}
              <section>
                <div className="mb-4">
                  <h4 className="text-lg font-semibold text-[#071B36]">
                    AI Authenticity Summary
                  </h4>
                  <p className="text-[11px] text-slate-400">Explain Score</p>
                </div>

                <div
                  className="bg-[#F7FAFF] border border-[#E2EBF8]
    rounded-[5px] px-4 sm:px-5 py-5"
                >
                  {(() => {
                    const text = String(aiSummary || "").trim();

                    // Detect generic uppercase headings, regardless of their names.
                    const headingPattern =
                      /(?:^|(?<=[.!?]\s))([A-Z][A-Z0-9]*(?:[\s-]+[A-Z0-9]+){1,7})(?=\s|:)/g;

                    const formattedText = text.replace(
                      headingPattern,
                      "\n$1\n",
                    );

                    const lines = formattedText
                      .split(/\n+/)
                      .map((line) => line.trim())
                      .filter(Boolean);

                    return (
                      <div className="space-y-3">
                        {lines.map((line, index) => {
                          const isHeading =
                            /^[A-Z][A-Z0-9]*(?:[\s-]+[A-Z0-9]+){1,7}:?$/.test(
                              line,
                            );

                          if (isHeading) {
                            return (
                              <h5
                                key={index}
                                className="text-[15px] font-bold uppercase
                  tracking-wide text-black pt-2 first:pt-0"
                              >
                                {line.replace(/:$/, "")}
                              </h5>
                            );
                          }

                          const isBullet = /^[-•*]\s*/.test(line);
                          const content = line.replace(/^[-•*]\s*/, "");

                          // Bold any short descriptive label before a colon.
                          const colonIndex = content.indexOf(":");
                          const hasLabel = colonIndex > 0 && colonIndex <= 45;

                          return (
                            <div
                              key={index}
                              className={`text-[13px] leading-[1.8]
                text-black-600 ${isBullet ? "flex gap-2" : ""}`}
                            >
                              {isBullet && (
                                <span className="text-[#0070E0] shrink-0">
                                  •
                                </span>
                              )}

                              <p>
                                {hasLabel ? (
                                  <>
                                    <strong className="font-semibold text-black">
                                      {content.slice(0, colonIndex + 1)}
                                    </strong>
                                    {content.slice(colonIndex + 1)}
                                  </>
                                ) : (
                                  content
                                )}
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })()}
                </div>
              </section>

              {/* Factors */}
              <section>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="text-xl font-medium text-[#071B36]">
                      Verified Signals
                    </h4>
                    <p className="text-[11px] text-black-400 mt-0.5">
                      Evidence collected during verification
                    </p>
                  </div>

                  <span className="text-[11px] text-black-400 font-medium">
                    {selectedOffer.trust?.factors?.length || 0} signals
                  </span>
                </div>

                <div
                  className="divide-y divide-slate-100 border-y
            border-slate-100"
                >
                  {(selectedOffer.trust?.factors || []).length === 0 ? (
                    <p className="text-xs text-black-400 py-5">
                      No individual factor signals recorded.
                    </p>
                  ) : (
                    (selectedOffer.trust?.factors || []).map((f, i) => {
                      let icon = "fa-question";
                      let iconColor = "text-slate-400";
                      let iconBg = "bg-slate-100";
                      let statusColor = "text-slate-500";
                      let statusLabel = "UNVERIFIED";

                      if (f.status === "ok") {
                        icon = "fa-check";
                        iconColor = "text-emerald-600";
                        iconBg = "bg-emerald-50";
                        statusColor = "text-emerald-700";
                        statusLabel = "VERIFIED";
                      } else if (f.status === "bad") {
                        icon = "fa-xmark";
                        iconColor = "text-rose-600";
                        iconBg = "bg-rose-50";
                        statusColor = "text-rose-700";
                        statusLabel = "CONCERN";
                      } else if (f.status === "warn") {
                        icon = "fa-exclamation";
                        iconColor = "text-amber-600";
                        iconBg = "bg-amber-50";
                        statusColor = "text-amber-700";
                        statusLabel = "LIMITED";
                      }

                      return (
                        <div key={i} className="py-4 flex items-start gap-3">
                          <div className="flex-1 min-w-0">
                            <div
                              className="flex items-center
                        justify-between gap-2"
                            >
                              <h5
                                className="text-[15px] font-medium
                          text-[#071B36]"
                              >
                                {f.name}
                              </h5>

                              <span
                                className={`text-[10px] font-bold
                          tracking-wide ${statusColor}`}
                              >
                                {statusLabel}
                              </span>
                            </div>

                            <p
                              className="text-xs text-black-500
                        leading-relaxed mt-1"
                            >
                              {f.detail}
                            </p>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </section>
            </div>

            {/* Footer */}
            <div
              className="px-5 sm:px-7 py-4 border-t
        border-slate-100 bg-white   flex justify-end shrink-0"
            >
              <button
                onClick={closeExplainModal}
                className="px-6 py-2.5 bg-gradient-to-r from-[#002990] to-[#0089FA]
           hover:bg-clip-text hover:text-transparent text-white hover:border-black-700 border border-2
          text-xs font-semibold rounded-[5px] transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* High Risk Gating Warning Modal (< 2.5 Score Second Confirm) */}
      {riskModalOpen && pendingRiskOffer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border-2 border-rose-200 text-center space-y-4">
            <div className="w-14 h-14 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center mx-auto text-2xl shadow-inner">
              <i className="fa-solid fa-triangle-exclamation"></i>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-900">
                High Risk Warning
              </h3>
              <p className="text-xs text-slate-600">
                This seller scored{" "}
                <span className="font-bold text-rose-600">
                  {pendingRiskOffer.trust?.score?.toFixed(1) || "1.9"} (Risky)
                </span>{" "}
                and has multiple authenticity red flags.
              </p>
            </div>

            <div className="bg-rose-50 border border-rose-100 rounded-xl p-3 text-left text-xs text-rose-900 space-y-1">
              <p className="font-semibold">Why this was flagged:</p>
              <p className="text-rose-800">
                {pendingRiskOffer.tradeoff_note ||
                  "Newly registered domain and lack of physical business verification."}
              </p>
            </div>

            <div className="space-y-2 pt-2">
              <button
                onClick={confirmRiskPayment}
                className="w-full bg-rose-600 hover:bg-rose-700 text-white font-semibold py-2.5 px-4 rounded-xl text-xs transition shadow-md"
              >
                I understand the risks, proceed to PayPal anyway
              </button>
              <button
                onClick={closeRiskModal}
                className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-2.5 px-4 rounded-xl text-xs transition"
              >
                Cancel (Recommended: Pick a Trusted Seller)
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
