import pandas as pd
from scrapers import get_newsletters_df, final_TLDR_extraction, final_MorningBrew_extraction, final_StartupPortugal_extraction
from pathlib import Path

def build_news_database(df_newsletters):
    """
    Iterates over each newsletter and applies the appropriate extractor.
    Returns a single concatenated DataFrame with all extracted news.
    """
    news_df = pd.DataFrame()

    for _, row in df_newsletters.iterrows():
        sender = row["from"].lower().strip()

        if sender == "dan@tldrnewsletter.com":
            extracted = final_TLDR_extraction(row)
        elif sender == "crew@morningbrew.com":
            # Ignore if it was issued on a sunday (it's a special edition with different format)
            if row["date"].weekday() == 6:
                continue
            extracted = final_MorningBrew_extraction(row)
        elif sender == "contact@startupportugal.com":
            extracted = final_StartupPortugal_extraction(row)
        else:
            continue
        
        news_df = pd.concat([news_df, extracted], ignore_index=True)

    return news_df


def main():
    """
    Main function to execute the database building process.
    1. Fetches raw newsletter data.
    2. Processes the raw data into a structured news database.
    3. Prints a summary of the result.
    """

    OUTPUT_PATH = Path(__file__).resolve().parent / "news_database.csv"

    # 1. Fetch raw newsletter data
    print("Step 1: Fetching raw newsletters...")
    try:
        df_newsletters = get_newsletters_df(label_name="Newsletters", days=30)
        print(f"   -> Successfully fetched {len(df_newsletters)} raw newsletters.")
    except Exception as e:
        print(f"   -> ERROR fetching newsletters: {e}")
        return

    # 2. Build the structured news database
    print("Step 2: Building structured news database...")
    news_database = build_news_database(df_newsletters)

    news_database.to_csv(OUTPUT_PATH, index=False)
    print("SCRAPPING FINISHED")



if __name__ == "__main__":
    main()