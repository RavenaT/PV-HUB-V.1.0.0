import os

import pandas as pd

from config import (
    MAX_EXCEL_SIZE_MB,
    DANGEROUS_EXCEL_PREFIXES,
)


class ExcelHandler:

    ADDRESS_COLUMN = "Alamat"

    # ========================================================
    # SECURITY
    # ========================================================

    @staticmethod
    def validate_file(filename):

        if not os.path.exists(filename):

            raise FileNotFoundError(
                f"File tidak ditemukan: {filename}"
            )

        size_mb = (
            os.path.getsize(filename)
            / 1024
            / 1024
        )

        if size_mb > MAX_EXCEL_SIZE_MB:

            raise ValueError(
                f"Ukuran Excel terlalu besar: "
                f"{size_mb:.2f} MB. "
                f"Maksimum {MAX_EXCEL_SIZE_MB} MB."
            )

    # ========================================================
    # SANITIZE
    # ========================================================

    @staticmethod
    def sanitize_cell(value):

        if pd.isna(value):

            return ""

        value = str(value)

        # Hindari formula injection
        if value.startswith(
            DANGEROUS_EXCEL_PREFIXES
        ):

            value = "'" + value

        return value.strip()

    # ========================================================
    # READ
    # ========================================================

    def read(self, filename):

        self.validate_file(
            filename
        )

        df = pd.read_excel(
            filename,
            engine="openpyxl"
        )

        if self.ADDRESS_COLUMN not in df.columns:

            raise ValueError(
                "Excel wajib memiliki kolom "
                "'Alamat'."
            )

        df[
            self.ADDRESS_COLUMN
        ] = df[
            self.ADDRESS_COLUMN
        ].apply(
            self.sanitize_cell
        )

        return df

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        dataframe,
        filename
    ):

        dataframe.to_excel(
            filename,
            index=False,
            engine="openpyxl"
        )