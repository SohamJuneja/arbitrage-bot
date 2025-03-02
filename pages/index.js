// pages/index.js
import { useState, useEffect, useRef } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
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
  // State
  const [opportunities, setOpportunities] = useState([]);
  const [trades, setTrades] = useState([]);
  const [marketData, setMarketData] = useState({});
  const [selectedPair, setSelectedPair] = useState('BTC/USDT');
  const [isConnected, setIsConnected] = useState(false);
  const [priceHistory, setPriceHistory] = useState([]);
  const [apiKey, setApiKey] = useState('');
  const wsRef = useRef(null);
  
  // Connect to WebSocket
  useEffect(() => {
    // WebSocket connection
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8000/ws');
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Try to reconnect after 2 seconds
        setTimeout(connectWebSocket, 2000);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'market_update') {
          setMarketData(data.data);
          
          // Update price history for charts
          if (data.data[selectedPair]) {
            const prices = data.data[selectedPair].prices;
            const timestamp = new Date().toLocaleTimeString();
            
            setPriceHistory(prev => {
              // Keep last 20 data points
              const newHistory = [...prev, { timestamp, prices }];
              if (newHistory.length > 20) {
                return newHistory.slice(newHistory.length - 20);
              }
              return newHistory;
            });
          }
        }
        
        if (data.type === 'arbitrage_opportunity') {
          setOpportunities(prev => {
            // Keep last 10 opportunities
            const newOpportunities = [data.data, ...prev];
            if (newOpportunities.length > 10) {
              return newOpportunities.slice(0, 10);
            }
            return newOpportunities;
          });
        }
        
        if (data.type === 'trade_execution') {
          setTrades(prev => {
            // Keep last 10 trades
            const newTrades = [data.data, ...prev];
            if (newTrades.length > 10) {
              return newTrades.slice(0, 10);
            }
            return newTrades;
          });
        }
      };
      
      return ws;
    };
    
    const ws = connectWebSocket();
    
    // Cleanup
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [selectedPair]);
  
  // Keep WebSocket alive
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 30000); // Every 30 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      if (!apiKey) return;
      
      try {
        // Fetch opportunities
        const oppsResponse = await fetch('http://localhost:8000/opportunities', {
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
        
        if (oppsResponse.ok) {
          const oppsData = await oppsResponse.json();
          setOpportunities(oppsData);
        }
        
        // Fetch trades
        const tradesResponse = await fetch('http://localhost:8000/trades', {
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
        
        if (tradesResponse.ok) {
          const tradesData = await tradesResponse.json();
          setTrades(tradesData);
        }
        
        // Fetch market data
        const marketResponse = await fetch('http://localhost:8000/market-data', {
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
        
        if (marketResponse.ok) {
          const marketData = await marketResponse.json();
          setMarketData(marketData);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };
    
    fetchData();
  }, [apiKey]);
  
  // Prepare chart data
  const chartData = {
    labels: priceHistory.map(item => item.timestamp),
    datasets: Object.keys(priceHistory[0]?.prices || {}).map((exchange, index) => ({
      label: exchange,
      data: priceHistory.map(item => item.prices[exchange]),
      borderColor: getColor(index),
      backgroundColor: getColor(index, 0.1),
      tension: 0.4
    }))
  };
  
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `${selectedPair} Price Comparison`,
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      }
    }
  };
  
  // Helper for chart colors
  function getColor(index, alpha = 1) {
    const colors = [
      `rgba(255, 99, 132, ${alpha})`,
      `rgba(54, 162, 235, ${alpha})`,
      `rgba(255, 206, 86, ${alpha})`,
      `rgba(75, 192, 192, ${alpha})`,
      `rgba(153, 102, 255, ${alpha})`,
    ];
    return colors[index % colors.length];
  }
  
  // Handle API key input
  const handleApiKeyChange = (e) => {
    setApiKey(e.target.value);
  };
  
  // Toggle automated trading
  const toggleTrading = async () => {
    if (!apiKey) return;
    
    try {
      const response = await fetch('http://localhost:8000/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          automated_trading: true // or false to disable
        })
      });
      
      if (response.ok) {
        alert('Trading configuration updated');
      } else {
        alert('Failed to update configuration');
      }
    } catch (error) {
      console.error('Error updating config:', error);
      alert('Error updating configuration');
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            AI-Powered DeFi Arbitrage Dashboard
          </h1>
          <div className="mt-2 flex items-center">
            <span className={`h-3 w-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span className="text-sm text-gray-500">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* API Key Input */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6 p-4">
          <div className="flex items-center">
            <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mr-4">
              API Key:
            </label>
            <input
              type="password"
              id="apiKey"
              value={apiKey}
              onChange={handleApiKeyChange}
              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
              placeholder="Enter API key"
            />
            <button
              onClick={toggleTrading}
              className="ml-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font