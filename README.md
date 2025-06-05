# ItineraAI

ItineraAI is a full-stack application that combines Next.js frontend with a Python FastAPI backend to provide intelligent itinerary planning and data analysis capabilities.

## Features

- Modern React-based frontend with Next.js
- FastAPI backend for efficient data processing
- Interactive data visualization with Recharts
- CSV data processing capabilities
- Responsive UI with Chakra UI
- TypeScript support for better development experience

## Tech Stack

### Frontend

- Next.js 15.3.3
- React 19
- TypeScript
- Chakra UI
- Recharts for data visualization
- Framer Motion for animations
- TailwindCSS for styling

### Backend

- FastAPI
- Python 3.x
- Uvicorn
- Pydantic for data validation
- HTTPX for async HTTP requests

## Prerequisites

- Node.js (v18 or higher)
- Python 3.x
- Git

## Installation

1. Clone the repository:

```bash
git clone https://github.com/abrahamlicona/ItineraAI.git
cd ItineraAI
```

2. Install frontend dependencies:

```bash
npm install
```

3. Set up Python virtual environment and install backend dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with necessary environment variables:

```env
# Add your environment variables here
```

## Development

1. Start the frontend development server:

```bash
npm run dev
```

2. Start the backend server:

```bash
uvicorn api:app --reload
```

The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:8000`.

## Building for Production

1. Build the frontend:

```bash
npm run build
```

2. Start the production server:

```bash
npm start
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Abraham Licona - [@abrahamlicona](https://github.com/abrahamlicona)

Project Link: [https://github.com/abrahamlicona/ItineraAI](https://github.com/abrahamlicona/ItineraAI)
