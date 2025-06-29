import csv
import os
import ncu_report

def parse_ncu_report(report_file, metrics, output_file="memsys_stats.out"):
    """
    Parses the NCU report, extracts metrics, saves results to CSV, and returns structured data for PatternConfig.
    
    :param report_file: Path to the NCU report file.
    :param metrics: List of metrics to extract (each metric is a dictionary with 'label' and 'name').
    :param output_file: Path to the CSV file to store results.
    :return: List of extracted metrics structured for PatternConfig.
    """
    try:
        # Load the NCU report
        context = ncu_report.load_report(report_file)
        print(f"Successfully loaded: {report_file}")

        # Prepare results for CSV and structured output
        results = []
        structured_data = []

        for range_idx in range(context.num_ranges()):
            my_range = context.range_by_idx(range_idx)
            print(f"\nProcessing Range {range_idx + 1}:")

            for action_idx in range(my_range.num_actions()):
                action = my_range.action_by_idx(action_idx)
                kernel_name = action.name()
                print(f"  Action {action_idx + 1} - Kernel: {kernel_name}")

                # Dictionary to store parsed metrics
                parsed_data = {"Kernel": kernel_name}
                pattern_data = {"Kernel": kernel_name}  # Data structured for PatternConfig

                # Extract specified metrics
                for metric in metrics:
                    label = metric['label']
                    metric_name = metric['name']
                    try:
                        value = action[metric_name].value()
                    except KeyError:
                        value = 0  # Default to 0 if metric is not found

                    print(f"    {label}: {value}")
                    parsed_data[label] = value
                    pattern_data[metric_name] = value  # Store in structured format

                # Append parsed data for this kernel
                results.append(parsed_data)
                structured_data.append(pattern_data)  # Store structured data

        # Check if file exists to determine if we should write headers
        file_exists = os.path.isfile(output_file)
        with open(output_file, mode='a', newline='') as csvfile:
            fieldnames = ["Kernel"] + [metric['label'] for metric in metrics]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header only if the file is new
            if not file_exists:
                writer.writeheader()

            # Write results
            for result in results:
                writer.writerow(result)

        print(f"Results saved to {output_file}")

        # Return structured data for PatternConfig
        return structured_data

    except Exception as e:
        print(f"Error parsing NCU report: {e}")
        raise

