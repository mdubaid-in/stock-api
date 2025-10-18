from typing import List, Dict
from db.mongoClient import stock_mongo_client
from log.logging import logger
from pymongo import UpdateOne


def save_stock_data(stock_data: List[Dict], batch_size: int = 1000):
    """Process in chunks for very large datasets"""

    # Filter valid stocks upfront
    valid_stocks = [
        stock
        for stock in stock_data
        if stock.get("_id") and (stock.get("nse_data") or stock.get("bse_data"))
    ]

    if not valid_stocks:
        logger.warning("No valid stock data to save")
        return True

    try:
        stocks = stock_mongo_client.get_collection("stocks")
        total_upserted = 0
        total_modified = 0

        # Process in chunks
        for i in range(0, len(valid_stocks), batch_size):
            chunk = valid_stocks[i : i + batch_size]
            bulk_operations = []

            for stock in chunk:
                # ... same logic as above ...
                _id = stock["_id"]
                update_doc = {}
                set_fields = {}
                addtoset_fields = {}

                for key, value in stock.items():
                    if key == "_id":
                        continue
                    elif key == "nse_data" and value:
                        addtoset_fields["nse_data"] = value
                    elif key == "bse_data" and value:
                        addtoset_fields["bse_data"] = value
                    else:
                        set_fields[key] = value

                if set_fields:
                    set_fields["_id"] = _id
                    update_doc["$set"] = set_fields
                else:
                    update_doc["$set"] = {"_id": _id}

                if addtoset_fields:
                    update_doc["$addToSet"] = addtoset_fields

                bulk_operations.append(UpdateOne({"_id": _id}, update_doc, upsert=True))

            result = stocks.bulk_write(bulk_operations, ordered=False)
            total_upserted += result.upserted_count
            total_modified += result.modified_count

        logger.debug(f"Total: {total_upserted} inserted, {total_modified} modified")

    except Exception as e:
        logger.error(f"Error saving stock data: {e}")
        return False

    return True


def get_stock_data(symbol: str):
    try:
        stocks = stock_mongo_client.get_collection("stocks")
        return stocks.find_one({"symbol": symbol})
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        return None
