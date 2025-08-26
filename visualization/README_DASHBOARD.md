# San-Xing Interactive Dashboard

A Streamlit-based web dashboard for visualizing your San-Xing personal analytics data.

## Features

- 📊 **Interactive Health Metrics**: Mood, energy, sleep quality, weight trends
- 🎯 **Activity Analysis**: Track positive/negative activities and their impact
- 🛌 **Sleep Patterns**: Sleep duration trends and quality correlations
- 📈 **Real-time Data**: Connect to Google Sheets or use JSON exports
- 🔄 **Auto-refresh**: Data updates every 5 minutes with caching
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

## Quick Start

### 1. Install Dependencies

```bash
# From the main San-Xing directory (not visualization subdirectory)
uv sync
```

### 2. Prepare Data

**Option A: Use JSON Export (Recommended for testing)**
```bash
# Make sure you have raw_data.json in the visualization directory
# If not, run the download script first
python download_data.py
```

**Option B: Connect to Google Sheets (Live Data)**
- Ensure your `../config.local.toml` is properly configured
- Make sure you have service account credentials in `../secrets/`

### 3. Run the Dashboard

```bash
# From the main directory
uv run python run_dashboard.py

# OR directly with streamlit
uv run streamlit run visualization/dashboard.py
```

The dashboard will be available at: `http://localhost:8501`

## Dashboard Sections

### 📊 Health Overview
- Real-time health metrics summary
- Multi-factor health dashboard with 6 key visualizations
- Correlation heatmap of all health indicators

### 🎯 Activities
- Activity trends over time (positive vs negative)
- Activity balance vs mood correlation
- Top 10 most common activities analysis

### 🛌 Sleep
- Sleep duration trends with recommended guidelines
- Sleep quality vs duration correlation
- Energy level integration

### 📈 Correlations
- Interactive correlation matrix
- Cross-metric analysis
- Pattern identification

## Deployment Options

### Option 1: Streamlit Cloud (Free)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Deploy with one click
5. Get a shareable public URL

### Option 2: Local Network Access

```bash
# Run on all network interfaces
uv run streamlit run dashboard.py --server.address 0.0.0.0
```

Access from other devices on your network: `http://YOUR_IP:8501`

### Option 3: Heroku Deployment

Create these files:

**requirements.txt**:
```
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.17.0
```

**Procfile**:
```
web: streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0
```

Deploy:
```bash
heroku create your-sanxing-dashboard
git add .
git commit -m "Add Streamlit dashboard"
git push heroku main
```

### Option 4: Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.address", "0.0.0.0"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./raw_data.json:/app/raw_data.json
      - ../config.local.toml:/app/config.local.toml
      - ../secrets:/app/secrets
```

## Configuration

### Data Sources

The dashboard supports two data sources:

1. **JSON File** (`raw_data.json`): Static export from your San-Xing data
2. **Google Sheets (Live)**: Real-time connection to your sheets

Switch between them using the sidebar dropdown.

### Customization

Edit `dashboard.py` to:
- Modify visualization styles
- Add new metrics
- Change color schemes
- Customize layouts

### Performance

- Data is cached for 5 minutes to improve performance
- Use the "Refresh Data" button to force updates
- Large datasets are automatically optimized

## Troubleshooting

### Common Issues

**"Data file not found"**
- Ensure `raw_data.json` exists in the visualization directory
- Run `python download_data.py` to generate it

**"Google Sheets connection failed"**
- Check your `config.local.toml` configuration
- Verify service account credentials
- Ensure proper permissions on the spreadsheet

**Slow loading**
- Clear cache using the refresh button
- Reduce date range in sidebar
- Check internet connection for live data

### Performance Tips

1. Use JSON mode for faster loading
2. Filter data by date range
3. Clear browser cache if needed
4. Use Chrome/Firefox for best performance

## Security Notes

- Keep `config.local.toml` and service account files secure
- Don't commit credentials to version control
- Use environment variables for production deployment
- Consider VPN for sensitive data access

## API Integration

The dashboard can be extended to integrate with:
- San-Xing Python CLI for fresh data processing
- Google Sheets API for real-time updates
- Export functions for generating reports
- Webhook endpoints for automatic updates

## Development

To extend the dashboard:

```bash
# Install development dependencies
uv add --dev streamlit-devtools

# Run in development mode
uv run streamlit run dashboard.py --server.runOnSave true
```

### Adding New Visualizations

1. Create processing function in dashboard.py
2. Add rendering function with plotly charts
3. Integrate into tab structure
4. Update sidebar controls if needed

### Custom Styling

Modify the CSS in the `st.markdown()` section for custom styling.