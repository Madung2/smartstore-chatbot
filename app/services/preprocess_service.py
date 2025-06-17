import os
import glob
import pandas as pd
from app.utils.preprocess import SmartstorePreprocessor

class PreprocessPipeline:
    def __init__(self, input_dir="app/datasets/csv", output_dir="app/datasets/processed_csv"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_csv_files(self):
        return glob.glob(os.path.join(self.input_dir, "*.csv"))

    def _process_file(self, csv_file):
        filename = os.path.basename(csv_file)
        pre = SmartstorePreprocessor(
            input_path=csv_file,
            output_path=os.path.join(self.output_dir, filename)
        )
        processed_df = pre.run()
        sample_data = []
        if not processed_df.empty:
            for _, row in processed_df.iterrows():
                sample_data.append(row)
        return filename, processed_df, sample_data

    def run(self):
        total_rows = 0
        processed_files = []
        csv_files = self._get_csv_files()
        for csv_file in csv_files:
            filename, processed_df, sample_data = self._process_file(csv_file)
            total_rows += len(processed_df)
            processed_files.append({
                "filename": filename,
                "data": sample_data
            })
        return {
            "message": "Preprocessing complete",
            "total_rows": total_rows,
            "processed_files": processed_files
        }
