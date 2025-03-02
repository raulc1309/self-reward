# selects from the eft dataset the entries with diff_score less than 0.25 (between the generated score and the score from the eft dataset)
# prepares the selected entries to be used in the sft training, by setting the prompt to be
# the llm as a judge prompt and the completion to be the score from the eft dataset
# the 2 sets are merged and used to generate the m1 model in 01_and_03_sft.py

import pandas as pd
import os

# Define constants for file paths
datasets_dir = "../datasets"

# dataset generated from 02_gen_eft_score.py, by asking the ift tuned model to evaluate the completions
eft_with_generated_score_file_path = os.path.join(datasets_dir, "02.0_eft_with_generated_score.jsonl")

# the set of entries with diff_score less than 0.25 (between the generated score and the score from the eft dataset)
eft_selected_file_path = os.path.join(datasets_dir, "02.1_eft_selected_dataset.jsonl")

# the set of based on previous file, with the prompt and completion fields modified to contain the llm as a judge prompt and the scrore from the eft dataset as completion (will be used for sft training)
eft_selected_prepared_file_path = os.path.join(datasets_dir, "02.1_eft_selected_prepared_dataset.jsonl")

# the ift dataset used in 01_and_03_sft.py
ift_file_path = os.path.join(datasets_dir, "00_ift.jsonl")
ift_and_eft_file_path = os.path.join(datasets_dir, "02.1_ift_and_eft.jsonl")

def read_jsonl_file(file_path):
    """Read a JSONL file into a pandas DataFrame."""
    return pd.read_json(file_path, lines=True)

def calculate_statistics(df):
    """Calculate and print statistics of the DataFrame."""
    total_entries = len(df)
    
    num_less_than_0_2 = len(df[df['diff_score'] < 0.2])
    num_less_than_0_25 = len(df[df['diff_score'] < 0.25])
    num_less_than_0_3 = len(df[df['diff_score'] < 0.3])
    num_null_diff_score = df['diff_score'].isnull().sum()

    print(f"Total entries: {total_entries}")
    print(f"Entries with diff_score < 0.2: {num_less_than_0_2}")
    print(f"Entries with diff_score < 0.25: {num_less_than_0_25}")
    print(f"Entries with diff_score < 0.3: {num_less_than_0_3}")
    print(f"Entries with null diff_score: {num_null_diff_score}")

def filter_and_save(df, threshold, file_path):
    """Filter DataFrame based on threshold and save to a file."""
    selected_df = df[df['diff_score'] < threshold]
    selected_df.to_json(file_path, orient='records', lines=True)
    return selected_df

def prepare_data(selected_df, template_file_path):
    # convert 0 to 1 range to 1 op 5 range
    def convert_range(x):
        return int(1 + (x + 0.05) * 4)

    """Prepare data by modifying prompt and completion fields."""
    file = open(template_file_path, 'r')
    template = file.read()
    file.close()

    new_dataset = []
    for index, row in selected_df.iterrows():
        prompt = template.format(prompt=row['prompt_text'], response=row['response_text'])
        completion = f"Score: {convert_range(row['quality_score'])}"

        new_dataset.append({'prompt': prompt, 'completion': completion})

    prepared_df = pd.DataFrame(new_dataset)
    return prepared_df

def merge_and_save(df1, df2, file_path):
    """Merge two DataFrames and save to a file."""
    merged_df = pd.concat([df1, df2])
    merged_df.to_json(file_path, orient='records', lines=True)

def main():
    df = read_jsonl_file(eft_with_generated_score_file_path)
    
    calculate_statistics(df)
    
    selected_df = filter_and_save(df, 0.25, eft_selected_file_path)
    prepared_df = prepare_data(selected_df, 'llm_as_a_judge_prompt.txt')
    prepared_df.to_json(eft_selected_prepared_file_path, orient='records', lines=True)
    
    ift_df = read_jsonl_file(ift_file_path)
    merge_and_save(ift_df, prepared_df, ift_and_eft_file_path)

if __name__ == "__main__":
    main()
