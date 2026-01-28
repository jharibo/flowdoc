"""Simple linear data import flow example.

Demonstrates a straightforward class-based flow with no branching:
read -> validate -> transform -> load.
"""

from flowdoc import flow, step


@flow(name="CSV Data Import", description="Import data from CSV files into the database")
class DataImporter:
    @step(name="Read CSV File", description="Read raw data from CSV file")
    def read_csv(self, file_path: str) -> list:
        return self.validate_data([])

    @step(name="Validate Data", description="Check data format and required fields")
    def validate_data(self, raw_data: list) -> list:
        return self.transform_data(raw_data)

    @step(name="Transform Data", description="Apply business rules and normalize data")
    def transform_data(self, valid_data: list) -> list:
        return self.load_to_database(valid_data)

    @step(name="Load to Database", description="Insert transformed records into database")
    def load_to_database(self, transformed_data: list) -> dict:
        return {"status": "imported", "count": len(transformed_data)}
