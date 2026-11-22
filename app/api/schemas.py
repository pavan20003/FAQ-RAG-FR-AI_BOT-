"""Validated request and response models for the HTTP API."""

from __future__ import annotations

import re
import unicodedata

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected text.")
    safe_chars = [char for char in value if not unicodedata.category(char).startswith("C")]
    return " ".join("".join(safe_chars).split())


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    session_id: str | None = Field(default=None, max_length=128)
    language: Literal["fr", "en"] = "fr"

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, value: object) -> str:
        question = _clean_text(value)
        if not question:
            raise ValueError("Veuillez saisir une question.")
        if len(question) > 500:
            raise ValueError("La question ne doit pas dépasser 500 caractères.")
        return question

    @field_validator("session_id", mode="before")
    @classmethod
    def clean_session_id(cls, value: object) -> str | None:
        if value is None:
            return None
        session_id = _clean_text(value)
        return session_id or None


class AnswerSource(BaseModel):
    citation: str
    title: str
    path: str
    page: int | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[AnswerSource]
    abstained: bool
    session_id: str


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    folder: str = "data/demo_site"

    @field_validator("folder", mode="before")
    @classmethod
    def clean_folder(cls, value: object) -> str:
        folder = _clean_text(value)
        if not folder:
            raise ValueError("Le dossier d'ingestion est obligatoire.")
        return folder


class IngestResponse(BaseModel):
    added: int
    updated: int
    skipped: int
    deleted: int
    chunks: int


class HandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=320)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("session_id", "email", "message", mode="before")
    @classmethod
    def clean_fields(cls, value: object) -> str:
        cleaned = _clean_text(value)
        if not cleaned:
            raise ValueError("Ce champ est obligatoire.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Veuillez saisir une adresse courriel valide.")
        return value


class HandoffResponse(BaseModel):
    status: str
