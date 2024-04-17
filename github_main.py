import time
from raydium_listings_github import RaydiumListingDataCollector
from data_analyzer import RaydiumListingDataAnalyzer
import asyncio
import multiprocessing

if __name__ == '__main__':

    controller = RaydiumListingDataCollector()
    asyncio.run(controller.main())



    while True:
        time.sleep(1)

