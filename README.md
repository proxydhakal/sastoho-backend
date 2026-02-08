# Mero Shopping - E-Commerce Platform

A modern full-stack e-commerce application built with FastAPI (backend) and React + TypeScript (frontend).

## 🚀 Features

- **User Management**: Registration, login, password recovery
- **Product Catalog**: Browse products, categories, search and filter
- **Shopping Cart**: Add to cart, guest cart support, quantity management
- **Wishlist**: Save favorite products
- **Order Management**: Place orders, track order status
- **Reviews & Ratings**: Product reviews and ratings
- **Admin Dashboard**: Manage products, orders, categories, and users
- **Payment Integration**: Stripe payment gateway (configured)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** (for backend)
- **Node.js 18+** and **npm** (for frontend)
- **PostgreSQL 15+** (or use Docker)
- **Redis** (or use Docker)
- **Docker & Docker Compose** (optional, for containerized setup)

## 🏗️ Project Structure

```
ecom-backend/
├── app/                    # Backend FastAPI application
│   ├── api/               # API routes
│   ├── core/              # Core configuration
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/           # Business logic
│   └── main.py            # FastAPI app entry point
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── components/    # Reusable components
│   │   ├── lib/           # API client and utilities
│   │   └── store/         # State management
│   └── package.json
├── alembic/               # Database migrations
├── template/              # HTML templates
├── docker-compose.yml     # Docker configuration
└── requirements.txt       # Python dependencies
```

## 🐳 Quick Start with Docker (Recommended)

The easiest way to run the entire application:

### 1. Clone the repository (if not already done)
```bash
cd ecom-backend
```

### 2. Create environment file
Create a `.env` file in the root directory:

```env
# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=Nitrogen@55
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=ecom_backend

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Redis
REDIS_URL=redis://redis:6379/0

# Email Configuration (for password reset)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Stripe (for payments)
STRIPE_API_KEY=your-stripe-api-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Token Expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Start all services
```bash
docker compose up -d
```

This will start:
- **Backend API**: http://localhost:8005
- **Frontend**: http://localhost:8090
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6380

### 4. Access the application
- **Frontend**: http://localhost:8090
- **Backend API**: http://localhost:8005
- **API Documentation**: http://localhost:8005/docs
- **Admin Panel**: http://localhost:8090/admin

### 5. Default Admin Credentials
After the initial setup, you can login with:
- **Email**: `proxydhakal@gmail.com`
- **Password**: `admin@123`

## 💻 Local Development Setup

### Backend Setup

#### 1. Install Python dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Setup PostgreSQL Database
```bash
# Create database
createdb ecom_backend

# Or using PostgreSQL client:
psql -U postgres
CREATE DATABASE ecom_backend;
```

#### 3. Configure environment variables
Create a `.env` file in the root directory (see Docker setup above for template).

For local development, update:
```env
POSTGRES_SERVER=localhost
REDIS_URL=redis://localhost:6379/0
```

#### 4. Run database migrations
```bash
# Run migrations
alembic upgrade head

# Create initial data (admin user, categories)
python -m app.initial_data
```

**Note:** If you encounter errors about missing `is_deleted` columns, make sure to run `alembic upgrade head` to apply all migrations including `b55f5ee61a4c_add_is_deleted_to_product_and_category.py`. The code will work without these columns (using hard deletes), but soft delete functionality requires the migration.

#### 4.1. Create Superuser (Optional)
```bash
# Create or update superuser account
python scripts/create_superuser.py

# Or on Windows:
scripts\create_superuser.bat

# Or on Linux/Mac:
bash scripts/create_superuser.sh
```

This will create/update a superuser with:
- **Email**: `proxydhakal@gmail.com`
- **Password**: `SpringWinter!`
- **Role**: `admin`
- **Is Superuser**: `True`

#### 5. Start the backend server
```bash
# Development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

# Alternative: Simple localhost only (faster for local dev)
uvicorn app.main:app --reload

# Production mode (no auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8005
```

**Command breakdown:**
- `app.main:app` - Module path and FastAPI app instance
- `--host 0.0.0.0` - Listen on all network interfaces (allows external access)
- `--port 8005` - Port number (default is 8000)
- `--reload` - Auto-reload on code changes (development only)

The backend will be available at: http://localhost:8005

### Frontend Setup

#### 1. Navigate to frontend directory
```bash
cd frontend
```

#### 2. Install dependencies
```bash
npm install
```

#### 3. Configure environment variables
Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8005
```

#### 4. Start the development server
```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

#### 5. Build for production (optional)
```bash
npm run build
npm run preview
```

## 🔧 Environment Variables

### Backend (.env in root)
| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | - |
| `POSTGRES_PASSWORD` | PostgreSQL password | - |
| `POSTGRES_SERVER` | PostgreSQL host | - |
| `POSTGRES_PORT` | PostgreSQL port | 5432 |
| `POSTGRES_DB` | Database name | - |
| `SECRET_KEY` | JWT secret key | - |
| `REDIS_URL` | Redis connection URL | - |
| `EMAIL_HOST` | SMTP server host | - |
| `EMAIL_PORT` | SMTP server port | - |
| `EMAIL_HOST_USER` | SMTP username | - |
| `EMAIL_HOST_PASSWORD` | SMTP password | - |
| `FROM_EMAIL` | Sender email address | - |
| `STRIPE_API_KEY` | Stripe API key | - |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | 30 |

### Frontend (.env in frontend/)
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | http://localhost:8000 |

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/users/` - User registration
- `POST /api/v1/auth/password-recovery/{email}` - Password recovery
- `POST /api/v1/auth/reset-password/` - Reset password

### Products
- `GET /api/v1/catalog/products` - List products
- `GET /api/v1/catalog/products/{id}` - Get product details
- `POST /api/v1/catalog/products` - Create product (admin)
- `DELETE /api/v1/catalog/products/{id}` - Delete product (admin)

### Cart
- `GET /api/v1/cart/` - Get cart
- `POST /api/v1/cart/items` - Add item to cart
- `PATCH /api/v1/cart/items/{item_id}` - Update cart item
- `DELETE /api/v1/cart/items/{item_id}` - Remove cart item

### Orders
- `GET /api/v1/orders/` - Get user orders
- `POST /api/v1/orders/` - Create order
- `GET /api/v1/orders/{id}` - Get order details

### Admin
- `GET /api/v1/admin/stats` - Get dashboard statistics
- `GET /api/v1/orders/admin/all` - Get all orders (admin)

Full API documentation available at: http://localhost:8005/docs

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🛠️ Troubleshooting

### Backend Issues

**Database connection error**
- Ensure PostgreSQL is running
- Check `.env` file has correct database credentials
- Verify database exists: `psql -U postgres -l`

**Migration errors**
```bash
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

**Port already in use**
- Change port in `docker-compose.yml` or use different port:
```bash
uvicorn app.main:app --port 8006 --reload
```

### Frontend Issues

**API connection errors**
- Verify backend is running on the correct port
- Check `VITE_API_URL` in `frontend/.env`
- Ensure CORS is configured correctly in backend

**Build errors**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Module not found errors**
```bash
# Reinstall dependencies
cd frontend
npm install
```

### Docker Issues

**Container won't start**
```bash
# Check logs
docker compose logs backend
docker compose logs frontend

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```

**Database connection in Docker**
- Ensure `POSTGRES_SERVER=db` (not `localhost`) in `.env`
- Wait for database to be ready before starting backend

## 📝 Development Workflow

1. **Start backend**: `uvicorn app.main:app --reload` (or `docker compose up backend`)
2. **Start frontend**: `cd frontend && npm run dev` (or `docker compose up frontend`)
3. **Make changes**: Both servers support hot-reload
4. **Run migrations**: `alembic upgrade head` (when schema changes)
5. **Test**: Use http://localhost:5173 for frontend, http://localhost:8005/docs for API

## 🚢 Production Deployment

### Backend
```bash
# Build Docker image
docker build -t ecom-backend .

# Run with production settings
docker run -p 8005:8005 --env-file .env.production ecom-backend
```

### Frontend
```bash
cd frontend
npm run build
# Serve the dist/ folder with nginx or similar
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [API Documentation](http://localhost:8005/docs) (when backend is running)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section above
- Check existing issues in the repository

---

**Happy Coding! 🎉**
