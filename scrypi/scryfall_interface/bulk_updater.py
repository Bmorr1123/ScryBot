import requests, json, os, datetime, time


class ScryfallBulkUpdater:
    def __init__(self):
        self.data_folder_path = "scryfall_data"
        self.bulk_metadata_path = os.path.join(self.data_folder_path, "bulk_metadata.json")
        self.bulk_data_url = "https://api.scryfall.com/bulk-data"
        self.bulk_data_type = "default_cards"
        self.headers = {"User-Agent": "ScryBot", "Accept": "application/json"}

        self.bulk_metadata = None
        self.load_bulk_metadata()

        self.bulk_data: None | dict | list = self.load_bulk_data()

    def check_if_bulk_data_is_old(self) -> bool:
        """
        This function checks the bulk metadata to see if the currently loaded bulk data is too old.
        If this functions returns true, then you should call load_bulk_metadata() to retrieve newer data.
        :return:
        """
        self.load_bulk_metadata()

        last_fetched: float = self.bulk_metadata["last_fetched"]
        if not last_fetched:  # If we have never fetched bulk data before
            return True

        last_fetched: datetime.datetime = datetime.datetime.fromtimestamp(last_fetched)
        # If local bulk data is too old
        if last_fetched < datetime.datetime.now() - datetime.timedelta(hours=8):
            return True

    def load_bulk_metadata(self):
        if not os.path.exists(self.bulk_metadata_path):
            if not os.path.exists(self.data_folder_path):
                os.mkdir(self.data_folder_path)
            print(f"Creating \"{self.bulk_metadata_path}\".")
            with open(self.bulk_metadata_path, "w+") as file:
                json.dump({"last_fetched": None, "data_path": None}, file, indent=4)

        # Load the meta
        with open(self.bulk_metadata_path, "r") as file:
            self.bulk_metadata = json.load(file)

    def load_bulk_data(self) -> dict:
        bulk_data = self.load_local_bulk_data()
        if bulk_data:
            print("Successfully loaded local bulk data!")
            return bulk_data

        bulk_data = self.download_bulk_data()
        if bulk_data:
            print("Successfully downloaded bulk data!")
            return bulk_data

        bulk_data = self.load_local_bulk_data(ignore_age=True)  # Failsafe to old data
        if bulk_data:
            return bulk_data

        # If we couldn't load local, download, or local old local, then we raise an error.
        raise Exception("Connection to Scryfall failed, and no local backup could be found.")

    def load_local_bulk_data(self, ignore_age=False, debug=True) -> None | dict:
        last_fetched: float = self.bulk_metadata["last_fetched"]
        if not last_fetched:  # If we have never fetched bulk data before
            if debug:
                print("No timestamp for previous fetch.")
            return

        last_fetched: datetime.datetime = datetime.datetime.fromtimestamp(last_fetched)
        # If local bulk data is too old
        if last_fetched < datetime.datetime.now() - datetime.timedelta(hours=8):
            if debug:
                print("Local bulk data is over 8 hours old.")
            if not ignore_age:
                return

        bulk_data_path: str = self.bulk_metadata["data_path"]
        if not bulk_data_path:  # If there is no path to data
            if debug:
                print("No path to local bulk data.")
            return

        bulk_data_path = bulk_data_path
        if not os.path.exists(bulk_data_path):  # If the file at the specified path is empty
            if debug:
                print(f"No file found at bulk data path.")
            return

        with open(bulk_data_path, "r") as file:
            return json.load(file)  # Success!

    def download_bulk_data(self) -> None | dict:
        response = requests.get(self.bulk_data_url, headers=self.headers)
        if response.status_code != 200:  # If it failed
            return
        # print(json.dumps(response.json(), indent=4))

        data: dict = response.json()
        if not data["data"]:
            return
        data = data["data"]
        download_uri: str | None = None
        for bulk_data_type in data:
            type = bulk_data_type["type"]
            if type == self.bulk_data_type:
                download_uri = bulk_data_type["download_uri"]

        if not download_uri:
            return

        file_path = os.path.join(self.data_folder_path, download_uri.split("/")[-1])
        if file_path == self.bulk_metadata["data_path"] and os.path.exists(file_path):
            print("Local bulk data file is in sync with remote bulk data.")
        else:
            start_time = time.time()
            print(f"Downloading new bulk data...")
            response = requests.get(download_uri, headers=self.headers)
            print(f"Finished downloading new bulk data! Elapsed Time: {time.time() - start_time:.2f} seconds")

            start_time = time.time()
            print("Saving new bulk data...")

            with open(file_path, "w") as file:
                json.dump(response.json(), file, indent=4)
            print(f"Saved new bulk data to \"{file_path}\"! Elapsed Time: {time.time() - start_time:.2f} seconds")

        # Update Metadata regardless
        last_fetched = datetime.datetime.now()
        with open(self.bulk_metadata_path, "w+") as file:
            json.dump(
                {"last_fetched": last_fetched.timestamp(), "data_path": file_path},
                file, indent=4
            )
        print("Saved new metadata.")

        return response.json()


if __name__ == "__main__":
    ScryfallBulkUpdater()