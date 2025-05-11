import uvicorn
import argparse
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Telegram Upload API server')
    parser.add_argument('--host', type=str, 
                       default=os.getenv('API_HOST', '0.0.0.0'),
                       help='Host to bind to')
    parser.add_argument('--port', type=int, 
                       default=int(os.getenv('API_PORT', '8000')),
                       help='Port to bind to')
    parser.add_argument('--reload', action='store_true',
                       help='Enable auto-reload on code changes')
    parser.add_argument('--log-level', type=str, 
                       default="info",
                       choices=["debug", "info", "warning", "error", "critical"],
                       help='Log level')
    args = parser.parse_args()
    
    # Configure Uvicorn logger
    log_level = getattr(logging, args.log_level.upper())
    
    # Run the application
    print(f"Starting Telegram Upload API on http://{args.host}:{args.port}")
    print(f"Log level: {args.log_level}")
    print(f"Auto-reload: {'enabled' if args.reload else 'disabled'}")
    
    uvicorn.run(
        "app.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level=args.log_level
    ) 