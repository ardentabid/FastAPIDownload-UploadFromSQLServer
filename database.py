from sqlalchemy import create_engine, text
import pandas as pd
from typing import List

class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)

    def get_tables(self) -> List[str]:
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            return [row[0] for row in result]

    def export_table_data(self, table_name: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        query = f"SELECT * FROM {table_name}"
        if start_date and end_date:
            query += f" WHERE created_date BETWEEN '{start_date}' AND '{end_date}'"
        
        return pd.read_sql(query, self.engine)

    def upload_file_to_table(self, file_path: str, table_name: str):
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        df.to_sql(table_name, self.engine, if_exists='append', index=False)