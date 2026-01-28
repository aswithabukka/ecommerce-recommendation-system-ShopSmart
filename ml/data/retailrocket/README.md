# RetailRocket Dataset

## Download Instructions

1. Create a Kaggle account at https://www.kaggle.com/

2. Get your API token:
   - Go to https://www.kaggle.com/settings
   - Click "Create New Token"
   - Save the downloaded `kaggle.json` to `~/.kaggle/`

3. Install Kaggle CLI:
   ```bash
   pip install kaggle
   ```

4. Download the dataset:
   ```bash
   kaggle datasets download -d retailrocket/ecommerce-dataset
   ```

5. Extract the files to this directory:
   ```bash
   unzip ecommerce-dataset.zip -d .
   ```

## Required Files

After extraction, you should have:
- `events.csv` - User behavior events (~2.7M records)
- `item_properties_part1.csv` - Product metadata (optional)
- `item_properties_part2.csv` - Additional product metadata (optional)
- `category_tree.csv` - Category hierarchy (optional)

## Data Structure

### events.csv
| Column | Type | Description |
|--------|------|-------------|
| timestamp | int | Unix timestamp in milliseconds |
| visitorid | int | Anonymous visitor ID |
| event | string | Event type: view, addtocart, transaction |
| itemid | int | Product ID |
| transactionid | int | Transaction ID (for purchases only) |

### category_tree.csv
| Column | Type | Description |
|--------|------|-------------|
| categoryid | int | Category ID |
| parentid | int | Parent category ID (null for root) |

## Loading the Data

After placing the files in this directory, run:

```bash
cd /path/to/shopsmart/ml
python -m data.seed.retailrocket_loader
```

Or with Docker:
```bash
docker exec shopsmart-ml python -m data.seed.retailrocket_loader
```

## Using Synthetic Data Instead

If you don't want to download the RetailRocket dataset, you can generate synthetic data:

```bash
python -m data.seed.synthetic_generator
```

Or with Docker:
```bash
docker exec shopsmart-ml python -m data.seed.synthetic_generator
```
