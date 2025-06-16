from fastapi import APIRouter
from app.services.preprocess import SmartstorePreprocessor
import os
import glob
import pandas as pd

router = APIRouter(prefix="/devops")

@router.post("/preprocess")
def run_preprocess():
    # try:
    input_dir = "app/datasets/csv"
    output_dir = "app/datasets/processed_csv"
    
    os.makedirs(output_dir, exist_ok=True)
    
    total_rows = 0
    processed_files = []
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        pre = SmartstorePreprocessor(
            input_path=csv_file,
            output_path=os.path.join(output_dir, filename)
        )
        processed_df = pre.run()
        total_rows += len(processed_df)
        if not processed_df.empty:
            sample_data = []
            for i, row in processed_df.iterrows():
                sample_data.append(row)
        processed_files.append(
            {
            "filename": filename,
            "data": sample_data
        }
        )
        
    return {
        "message": "Preprocessing complete",
        "total_rows": total_rows,
        "processed_files": processed_files
    }
        
    # except Exception as e:
    #     return {
    #         "message": "Error during preprocessing",
    #         "error": str(e),
    #         "total_rows": total_rows if 'total_rows' in locals() else 0,
    #         "processed_files": processed_files if 'processed_files' in locals() else []
    #     }
