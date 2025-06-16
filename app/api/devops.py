from fastapi import APIRouter
from app.services.preprocess import SmartstorePreprocessor
import os
import glob

router = APIRouter(prefix="/devops")

@router.post("/preprocess") 
def run_preprocess():
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
        num_rows = pre.run()
        total_rows += num_rows
        processed_files.append(
            {
            "filename": filename,
            "data": pre.preprocess_row(pre.df.iloc[0]) if num_rows > 0 else {}
        }
        )
        
    return {
        "message": "Preprocessing complete",
        "total_rows": total_rows,
        "processed_files": processed_files
    }
