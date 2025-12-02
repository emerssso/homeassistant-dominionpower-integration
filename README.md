# Dominion Energy Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration to fetch energy usage, costs, and billing data from Dominion Energy.

## Features

- **Grid Consumption** - Track your energy consumption from the grid (kWh)
- **Grid Return** - Track energy returned to the grid for solar customers (kWh)
- **Current Bill Cost** - Monitor your current billing period cost (USD)
- **Billing Period** - View billing period start and end dates
- **Current Rate** - Track your current electricity rate ($/kWh)
- **Energy Dashboard Compatible** - All sensors work with Home Assistant's Energy Dashboard

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/walljm/homeassistant-dominionpower-integration`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "Dominion Energy" in HACS
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/dominion_energy` folder from this repository
2. Copy it to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

You'll need the following information from your Dominion Energy account:

1. **Username** - Your Dominion Energy account email
2. **Password** - Your Dominion Energy account password
3. **Account Number** - Your Dominion Energy account number (found on your bill)

### Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Dominion Energy"
4. Enter your credentials and account number
5. Click **Submit**

## Sensors

| Sensor | Description | Device Class | Unit |
|--------|-------------|--------------|------|
| Grid Consumption | Total energy consumed from grid | `energy` | kWh |
| Grid Return | Total energy returned to grid | `energy` | kWh |
| Current Bill | Current billing period cost | `monetary` | USD |
| Billing Period Start | Start date of current billing period | `date` | - |
| Billing Period End | End date of current billing period | `date` | - |
| Current Rate | Current electricity rate | - | $/kWh |
| Daily Cost | Estimated daily energy cost | `monetary` | USD |
| Monthly Usage | Month-to-date energy usage | `energy` | kWh |

## Energy Dashboard

To add this integration to your Energy Dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Under "Grid consumption", click **Add consumption**
3. Select the "Dominion Energy Grid Consumption" sensor
4. Under "Return to grid" (if applicable), click **Add return**
5. Select the "Dominion Energy Grid Return" sensor

## Troubleshooting

### Authentication Issues

- Ensure your username and password are correct
- Check that your account number matches what's on your bill
- The integration may need to be reconfigured if Dominion Energy changes their API

### Data Not Updating

- Dominion Energy typically updates usage data once per day
- The integration polls for new data every 12 hours by default
- Check the Home Assistant logs for any error messages

### Rate Limiting

The integration is designed to poll infrequently to avoid rate limiting. If you experience issues, try increasing the scan interval.

## API Information

This integration uses Dominion Energy's internal API:
- Login: `https://login.dominionenergy.com/CommonLogin`
- API Base: `https://prodsvc-dominioncip.smartcmobile.com/Service/api/1/`

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with, endorsed by, or connected to Dominion Energy. Use at your own risk.
