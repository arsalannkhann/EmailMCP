#!/bin/bash

# EmailMCP Sample Frontend Setup Script

echo "=========================================="
echo "EmailMCP Sample Frontend Setup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: This script must be run from the sample-frontend directory"
    exit 1
fi

echo "✅ Found frontend files"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python found: $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Please install Python 3"
    exit 1
fi

# Check Node (optional)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js found: $NODE_VERSION"
else
    echo "⚠️  Node.js not found (optional)"
fi

echo ""
echo "=========================================="
echo "Setup Options:"
echo "=========================================="
echo ""
echo "1. Serve with Python (recommended)"
echo "2. Serve with Node.js"
echo "3. Setup backend proxy (requires Node.js)"
echo "4. Run connection tests"
echo "5. Exit"
echo ""
read -p "Select option (1-5): " option

case $option in
    1)
        echo ""
        echo "Starting Python HTTP server on port 8000..."
        echo "Open http://localhost:8000 in your browser"
        echo "Press Ctrl+C to stop"
        echo ""
        python3 -m http.server 8000
        ;;
    2)
        if ! command -v npx &> /dev/null; then
            echo "❌ npx not found. Please install Node.js first"
            exit 1
        fi
        echo ""
        echo "Starting Node.js HTTP server on port 8000..."
        echo "Open http://localhost:8000 in your browser"
        echo "Press Ctrl+C to stop"
        echo ""
        npx http-server -p 8000
        ;;
    3)
        echo ""
        echo "Setting up backend proxy..."
        if [ ! -d "backend-proxy" ]; then
            echo "❌ backend-proxy directory not found"
            exit 1
        fi
        cd backend-proxy
        
        if [ ! -f ".env" ]; then
            echo "Creating .env file..."
            cp .env.example .env
            echo "✅ Created .env file. Please edit it with your configuration."
        fi
        
        echo "Installing dependencies..."
        npm install
        
        echo ""
        echo "✅ Backend proxy setup complete!"
        echo ""
        echo "To start the backend proxy:"
        echo "  cd backend-proxy"
        echo "  npm start"
        echo ""
        ;;
    4)
        echo ""
        echo "Opening connection test page..."
        if command -v python3 &> /dev/null; then
            echo "Starting server on port 8000..."
            echo "Open http://localhost:8000/test-connection.html in your browser"
            python3 -m http.server 8000
        else
            echo "Please run the server manually and open test-connection.html"
        fi
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac
