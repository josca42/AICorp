from typing import Generic, Type, TypeVar, List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json
import pandas as pd
from .db import docs_db, chroma_client
from . import models

ModelType = TypeVar("ModelType")
CollectionType = TypeVar("CollectionType")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1_000,
    chunk_overlap=200,
    length_function=len,
)


class CRUDBase(Generic[ModelType, CollectionType]):
    def __init__(self, model: Type[ModelType], collection: Type[CollectionType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A model class
        * `collection`: A Chroma collection
        """
        self.model = model
        self.collection = collection

    def get(self, id) -> ModelType:
        return self.collection.get(ids=[id], include=["documents"])[0]

    def create(self, obj: ModelType) -> ModelType:
        self._add(obj, "create")

    def upsert(self, obj: ModelType) -> ModelType:
        doc = self.get(obj.id)
        if doc:
            if doc.timestamp > obj.timestamp:
                self.update(obj)
            else:
                pass
        else:
            self.create(obj)

    def update(self, obj: ModelType) -> ModelType:
        self._add(obj, "update")

    def delete(self, id) -> None:
        self.collection.delete(ids=[id])

    def where(self, equals: dict = {}) -> pd.DataFrame:
        if self.model.source != "doc":
            equals = equals.copy()
            equals["source"] = self.model.source
        rows = self.collection.get(where=equals)
        return pd.DataFrame(
            [
                self.model(content=doc, **metas).dict()
                for doc, metas in zip(rows["documents"], rows["metadatas"])
            ]
        )

    def _add(self, obj: ModelType, add_op: str):
        if obj.content:
            obj_dict = json.loads(obj.json())
            obj_dict["source"] = self.model.source
            text = obj_dict.pop("content")
            _id = obj_dict["id"]
            text_chunks = text_splitter.split_text(text)
            idx_chunks = range(len(text_chunks))
            chroma_data = dict(
                documents=text_chunks,
                metadatas=[obj_dict for i in idx_chunks],
                ids=[_id + "-" + str(i) for i in idx_chunks]
                if len(text_chunks) > 1
                else [_id],
            )
            if add_op == "create":
                self.collection.add(**chroma_data)
            elif add_op == "update":
                self.collection.update(**chroma_data)
            else:
                raise ValueError("add_op must be 'create' or 'update'")
            chroma_client.persist()


discord = CRUDBase(models.Discord, docs_db)
