# Running Initial Data Script

## Automatic (Recommended)
The script runs automatically when you start the backend container:
```bash
docker compose up -d
```

## Manual Execution

### Inside Docker Container
```bash
# Enter the container
docker compose exec backend bash

# Run from project root (/app)
cd /app
python -m app.initial_data
```

### Outside Docker (Local Development)
```bash
# From project root
python -m app.initial_data

# Or directly
python app/initial_data.py
```

## What It Creates
- **Admin User**: admin@example.com / admin123
- **Categories**: Electronics, Clothing, Home & Garden

## Troubleshooting

**Error: "No module named 'app'"**
- Make sure you're in the `/app` directory (project root)
- Use `python -m app.initial_data` instead of `python app/initial_data.py`

**Error: "User already exists"**
- The script is idempotent - it won't create duplicates
- Admin already exists, you can proceed
