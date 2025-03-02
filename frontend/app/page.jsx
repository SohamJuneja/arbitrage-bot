"use client";
import { useState, useEffect, useRef } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function Dashboard() {
  const [opportunities, setOpportunities] = useState([]);
  const [trades, setTrades] = useState([]);
  const [marketData, setMarketData] = useState({});
  const [selectedPair, setSelectedPair] = useState("BTC/USDT");
  const [isConnected, setIsConnected] = useState(false);
  const [priceHistory, setPriceHistory] = useState([]);
  const [apiKey, setApiKey] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket("ws://localhost:8000/ws");
      wsRef.current = ws;

      ws.onopen = () => setIsConnected(true);
      ws.onclose = () => {
        setIsConnected(false);
        setTimeout(connectWebSocket, 2000);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "market_update") {
          setMarketData(data.data);

          if (data.data[selectedPair]) {
            const prices = data.data[selectedPair].prices;
            const timestamp = new Date().toLocaleTimeString();

            setPriceHistory((prev) => {
              const newHistory = [...prev, { timestamp, prices }];
              return newHistory.slice(-20);
            });
          }
        }

        if (data.type === "arbitrage_opportunity") {
          setOpportunities((prev) => [data.data, ...prev].slice(0, 10));
        }

        if (data.type === "trade_execution") {
          setTrades((prev) => [data.data, ...prev].slice(0, 10));
        }
      };
    };

    connectWebSocket();
    return () => wsRef.current?.close();
  }, [selectedPair]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      if (!apiKey) return;
      try {
        const headers = { Authorization: `Bearer ${apiKey}` };
        const endpoints = ["opportunities", "trades", "market-data"];
        const responses = await Promise.all(
          endpoints.map((endpoint) =>
            fetch(`http://localhost:8000/${endpoint}`, { headers })
          )
        );

        const [oppsData, tradesData, marketData] = await Promise.all(
          responses.map((res) => (res.ok ? res.json() : []))
        );
        setOpportunities(oppsData);
        setTrades(tradesData);
        setMarketData(marketData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };
    fetchData();
  }, [apiKey]);

  const getColor = (index, alpha = 1) => {
    const colors = [
      `rgba(255, 99, 132, ${alpha})`,
      `rgba(54, 162, 235, ${alpha})`,
      `rgba(255, 206, 86, ${alpha})`,
      `rgba(75, 192, 192, ${alpha})`,
      `rgba(153, 102, 255, ${alpha})`,
    ];
    return colors[index % colors.length];
  };

  const chartData = {
    labels: priceHistory.map((item) => item.timestamp),
    datasets: Object.keys(priceHistory[0]?.prices || {}).map(
      (exchange, index) => ({
        label: exchange,
        data: priceHistory.map((item) => item.prices[exchange]),
        borderColor: getColor(index),
        backgroundColor: getColor(index, 0.1),
        tension: 0.4,
      })
    ),
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: `${selectedPair} Price Comparison` },
    },
    scales: { y: { beginAtZero: false } },
  };

  const handleApiKeyChange = (e) => setApiKey(e.target.value);

  const toggleTrading = async () => {
    if (!apiKey) return;
    try {
      const response = await fetch("http://localhost:8000/config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ automated_trading: true }),
      });
      alert(
        response.ok
          ? "Trading configuration updated"
          : "Failed to update configuration"
      );
    } catch (error) {
      console.error("Error updating config:", error);
      alert("Error updating configuration");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow p-6">
        <h1 className="text-3xl font-bold">
          AI-Powered DeFi Arbitrage Dashboard
        </h1>
        <div className="mt-2 flex items-center">
          <span
            className={`h-3 w-3 rounded-full ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          ></span>
          <span className="ml-2 text-sm">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 px-4">
        <div className="bg-white shadow p-4 rounded-lg mb-6">
          <label htmlFor="apiKey" className="block text-sm font-medium mb-2">
            API Key:
          </label>
          <input
            type="password"
            id="apiKey"
            value={apiKey}
            onChange={handleApiKeyChange}
            placeholder="Enter API key"
            className="w-full p-2 border rounded"
          />
        </div>

        <button
          onClick={toggleTrading}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Toggle Trading
        </button>

        <div className="bg-white shadow p-6 mt-6 rounded-lg">
          <Line data={chartData} options={chartOptions} />
        </div>
      </main>
    </div>
  );
}
