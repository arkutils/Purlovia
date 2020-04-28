from typing import *

import requests

from utils.log import get_logger

logger = get_logger(__name__)


class SteamApiException(Exception):
    pass


class SteamApi:
    API_URL = 'https://api.steampowered.com'

    @staticmethod
    def _createUrl(interface: str, method: str, version: int = 1):
        return f'{SteamApi.API_URL}/{interface}/{method}/v{version}/'

    @classmethod
    def GetPublishedFileDetails(cls, mods: Iterable[str]) -> Dict:
        url = cls._createUrl('ISteamRemoteStorage', 'GetPublishedFileDetails')
        params: Dict[str, Any] = dict((f'publishedfileids[{i}]', modid) for (i, modid) in enumerate(mods))
        params['itemcount'] = len(params)
        logger.debug(f'POST {url} {params}')
        req = requests.post(url, data=params)
        if req.status_code != 200:
            raise SteamApiException(f'GetPublishedFileDetails returned status {req.status_code}')
        return req.json()['response']['publishedfiledetails']


# https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/ (https://steamapi.xpaw.me/#ISteamRemoteStorage)
# itemcount=N
# publishedfileids[0..i]=mod_id

# {
#    "response": {
#        "result": 1,
#        "resultcount": 2,
#        "publishedfiledetails": [
#             "publishedfileid": "893735676",
#             "result": 1,
#             "creator": "76561198063282150",
#             "creator_app_id": 346110,
#             "consumer_app_id": 346110,
#             "filename": "",
#             "file_size": 2904550186,
#             "file_url": "",
#             "hcontent_file": "3591238750483982181",
#             "preview_url": "https://steamuserimages-a.akamaihd.net/ugc/811121990162311337/BF23A0BB916BD1076AED20446A0C257674BCB5D4/",
#             "hcontent_preview": "811121990162311337",
#             "title": "Ark Eternal (Live Version)",
#             "description": "...massive snip...",
#             "time_created": 1490769234,
#             "time_updated": 1560939016,
#             "visibility": 0,
#             "banned": 0,
#             "ban_reason": "",
#             "subscriptions": 51802,
#             "favorited": 907,
#             "lifetime_subscriptions": 67592,
#             "lifetime_favorited": 1004,
#             "views": 35813,
#             "tags": []
