from typing import List
from pydantic import BaseModel, ConfigDict, Field


class JsonSerializable(BaseModel):
        
    def to_json(self):
        return self.model_dump_json()


class OrchestratorIn(JsonSerializable):
    callback_uri_template: str
    client_input: dict

    @staticmethod
    def from_json(obj: str):
        return OrchestratorIn.model_validate_json(obj)


class GeocodingOut(JsonSerializable):
    model_config = ConfigDict()
    place_id: int
    licence: str
    powered_by: str
    osm_type: str
    osm_id: int
    boundingbox: List[str]
    lat: str
    lon: str
    display_name: str
    # class_: str = Field(..., alias='class', validation_alias="class")
    type: str
    importance: float

    @staticmethod
    def from_json(obj: dict):
        return GeocodingOut.model_validate_json(obj)


class WeatherIn(JsonSerializable):
    lat: str
    lon: str

    @staticmethod
    def from_json(obj: str):
        return WeatherIn.model_validate_json(obj)


class WeatherCurrentUnits(BaseModel):
    time: str
    interval: str
    temperature: str


class WeatherCurrent(BaseModel):
    time: str
    interval: int
    temperature: float


class WeatherOut(JsonSerializable):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    current_units: WeatherCurrentUnits
    current: WeatherCurrent

    @staticmethod
    def from_json(obj: str):
        return WeatherOut.model_validate_json(obj)


class FeedbackReq(JsonSerializable):
    output: dict
    callback_uri: str

    @staticmethod
    def from_json(obj: str):
        return FeedbackReq.model_validate_json(obj)


class FeedbackRsp(JsonSerializable):
    status: str

    @staticmethod
    def from_json(obj: str):
        return FeedbackRsp.model_validate_json(obj)


class WorkflowOut(JsonSerializable):
    destination: str
    lat: str
    lon: str
    current_temp: float

    @staticmethod
    def from_json(obj: str):
        return WorkflowOut.model_validate_json(obj)


class OrchesratorOut(JsonSerializable):
    workflow: WorkflowOut
    feedback: FeedbackRsp

    @staticmethod
    def from_json(obj: str):
        return OrchesratorOut.model_validate_json(obj)

