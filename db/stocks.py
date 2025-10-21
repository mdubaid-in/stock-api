from turtle import update
from typing import List, Dict
from db.mongoClient import stock_mongo_client
from log.logging import logger
from pymongo import UpdateOne


def save_stock_data(stock_data: List[Dict]):
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
        collection = stock_mongo_client.get_collection("stocks")
        total_upserted = 0
        total_modified = 0
        bulk_operations = []

        # Process in chunks
        for stock in valid_stocks:
            _id = stock["_id"]
            update_doc = {}
            set_fields = {}
            add_to_set_fields = {}

            for key, value in stock.items():
                if key == "_id":
                    continue
                elif key not in ("nse_data", "bse_data"):
                    set_fields[key] = value
                elif value:
                    add_to_set_fields[key] = value

            if add_to_set_fields:
                update_doc["$push"] = add_to_set_fields

            if set_fields:
                update_doc["$setOnInsert"] = set_fields

            bulk_operations.append(UpdateOne({"_id": _id}, update_doc, upsert=True))

        if bulk_operations:
            result = collection.bulk_write(bulk_operations, ordered=False)
            total_upserted += result.upserted_count
            total_modified += result.modified_count

        logger.note(f"Total: {total_upserted} inserted, {total_modified} modified")

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
