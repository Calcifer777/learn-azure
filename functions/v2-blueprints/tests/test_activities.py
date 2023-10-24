import re
from polyfactory.factories.pydantic_factory import ModelFactory
import pytest

from models import *
from activities import (
    get_city_weather,
    get_geocoding,
)

class GeocodingOutFactory(ModelFactory[GeocodingOut]):
    __model__ = GeocodingOut


class WeatherOutFactory(ModelFactory[WeatherOut]):
    __model__ = WeatherOut


@pytest.mark.asyncio
async def test_get_geocoding(aioresponse):
    rsp: GeocodingOut = GeocodingOutFactory.build()
    aioresponse.get(re.compile(".*"), status=200, payload=[rsp.model_dump()])
    fn = get_geocoding.build().get_user_function()
    out = await fn("new york")
    assert type(out) == GeocodingOut


@pytest.mark.asyncio
async def test_get_weather(aioresponse):
    rsp: WeatherOut = WeatherOutFactory.build()
    aioresponse.get(re.compile(".*"), status=200, payload=rsp.model_dump())
    fn = get_city_weather.build().get_user_function()
    in_ = WeatherIn(lat="90.0", lon="90")
    out = await fn(in_.model_dump())
    assert type(out) == WeatherOut
