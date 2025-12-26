from typing import List

from pydantic import BaseModel


class PrepareData(BaseModel):

    question: str
    answer: str
    scene: str = None


class PrepareUpdateParam(BaseModel):

    insert_list: List[PrepareData] = []
    update_list: List[PrepareData] = []
    delete_list: List[str] = []
