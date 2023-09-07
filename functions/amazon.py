from decouple import config
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException
import json
import math
import enum

Categories = enum.Enum('Categories', ['Automotive', 'Baby', 'Beauty', 'Books', 'Computers', 'Electronics', 'EverythingElse', 'Fashion', 'GiftCards', 'HealthPersonalCare', 'HomeAndKitchen', 'KindleStore',
                       'Lighting', 'Luggage', 'MobileApps', 'MoviesAndTV', 'Music', 'OfficeProducts', 'PetSupplies', 'Software', 'SportsAndOutdoors', 'ToolsAndHomeImprovement', 'ToysAndGames', 'VideoGames'])

ACCESS_KEY = config('AMZN_ACCESS_KEY_ID')
SECRET = config('AMZN_SECRET')


def get_amazon_product(keywords, category, max, min, brand):
    # print("Searching for:", keywords, category, budget, brand)
    partner_tag = "gignius-22"

    host = "webservices.amazon.com.au"
    url = "amazon.com.au/dp"
    region = "us-west-2"
    ACCESS_KEY = config('AMZN_ACCESS_KEY_ID')
    SECRET = config('AMZN_SECRET')

    """ API declaration """
    default_api = DefaultApi(
        access_key=ACCESS_KEY, secret_key=SECRET, host=host, region=region
    )

    search_items_resource = [
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.IMAGES_PRIMARY_MEDIUM,
    ]

    """ Forming request """
    try:
        if brand and float(min) > 0.0 and float(max) > 0.0:
            search_items_request = SearchItemsRequest(
                partner_tag=partner_tag,
                partner_type=PartnerType.ASSOCIATES,
                keywords=keywords,
                search_index=category,
                item_count=3,
                brand=brand,
                resources=search_items_resource,
                max_price=int(float(max) * 100),
                min_price=int(float(min) * 100),
            )
        elif brand and min == "0" and float(max) > 0.0:
            search_items_request = SearchItemsRequest(
                partner_tag=partner_tag,
                partner_type=PartnerType.ASSOCIATES,
                keywords=keywords,
                search_index=category,
                item_count=3,
                brand=brand,
                resources=search_items_resource,
                max_price=int(float(max) * 100),
            )
        elif float(min) > 0.0 and float(max) > 0.0:
            search_items_request = SearchItemsRequest(
                partner_tag=partner_tag,
                partner_type=PartnerType.ASSOCIATES,
                keywords=keywords,
                search_index=category,
                item_count=3,
                resources=search_items_resource,
                max_price=int(float(max) * 100),
                min_price=int(float(min) * 100),
            )
        elif float(max) > 0.0:
            search_items_request = SearchItemsRequest(
                partner_tag=partner_tag,
                partner_type=PartnerType.ASSOCIATES,
                keywords=keywords,
                search_index=category,
                item_count=3,
                resources=search_items_resource,
                max_price=int(float(max) * 100),
            )
        else:
            search_items_request = SearchItemsRequest(
                partner_tag=partner_tag,
                partner_type=PartnerType.ASSOCIATES,
                keywords=keywords,
                search_index=category,
                item_count=3,
                resources=search_items_resource,
            )
    except ValueError as exception:
        print("Error in forming SearchItemsRequest: ", exception)
        return

    try:
        """ Sending request """
        response = default_api.search_items(
            search_items_request)

        print("API called Successfully")
        print("Complete Response:", response)

        """ Parse response """
        if response.search_result is not None:
            res = []
            for item in response.search_result.items:
                if item.detail_page_url.find(url) > -1:
                    available = item.offers.listings[0].availability
                    if available is not None:
                        available = available.message
                    else:
                        available = ""

                    res.append({'affiliate_url': item.detail_page_url, 'image_url': item.images.primary.medium.url,
                                'price': item.offers.listings[0].price.display_amount, 'availability': available,
                                'item_info': item.item_info.title.display_value})
            return json.dumps(res)
            print("Printing first item information in SearchResult:")
            item_0 = response.search_result.items[0]
            if item_0 is not None:
                if item_0.asin is not None:
                    print("ASIN: ", item_0.asin)
                if item_0.detail_page_url is not None:
                    print("DetailPageURL: ", item_0.detail_page_url)
                if (
                    item_0.item_info is not None
                    and item_0.item_info.title is not None
                    and item_0.item_info.title.display_value is not None
                ):
                    print("Title: ", item_0.item_info.title.display_value)
                if (
                    item_0.offers is not None
                    and item_0.offers.listings is not None
                    and item_0.offers.listings[0].price is not None
                    and item_0.offers.listings[0].price.display_amount is not None
                ):
                    print(
                        "Buying Price: ", item_0.offers.listings[0].price.display_amount
                    )
        if response.errors is not None:
            print("\nPrinting Errors:\nPrinting First Error Object from list of Errors")
            print("Error code", response.errors[0].code)
            print("Error message", response.errors[0].message)
            return "There was an error with your search."

    except ApiException as exception:
        print("Error calling PA-API 5.0!")
        print("Status code:", exception.status)
        print("Errors :", exception.body)
        print("Request ID:", exception.headers["x-amzn-RequestId"])

    except TypeError as exception:
        print("TypeError :", exception)

    except ValueError as exception:
        print("ValueError :", exception)

    except Exception as exception:
        print("Exception :", exception)
