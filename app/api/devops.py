from fastapi import APIRouter, HTTPException
from app.utils.preprocess import SmartstorePreprocessor
from app.services import preprocess_service
from app.services.embedding_service import EmbeddingPipeline
from app.services.preprocess_service import PreprocessPipeline
import os
import glob
import pandas as pd
from tqdm import tqdm
import time
import logging

router = APIRouter(prefix="/devops")
logger = logging.getLogger(__name__)

@router.post("/preprocess")
def run_preprocess():
    pre = PreprocessPipeline()
    return pre.run()

@router.post("/embed")
def embed_csv(filename: str = "final_result.csv", batch_size: int = 100):
    emb = EmbeddingPipeline(batch_size=batch_size)
    return emb.run(filename)