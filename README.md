# WALL-E

## Overview

WALL-E is a cutting-edge project that leverages rule learning to align Large Language Models (LLMs) with environment dynamics, enhancing their performance as world models for model-based agents. By integrating learned rules, WALL-E bridges the gap between the inherent knowledge of LLMs and various environments, resulting in more accurate state predictions and optimized action sequences.

## Demo Release

The current repository includes a demo that allows users to apply rule learning to their own collected trajectories.

### Preparing Trajectories

To perform rule learning, you need to provide trajectories collected from your environment. Trajectories should be saved in JSON format following the structure below:

```json
{
    "action_type_1": [
        {
            "state": { /* state details */ },
            "action": { /* action details */ },
            "action_result": { /* result details */ }
        },
        {
            "state": { /* state details */ },
            "action": { /* action details */ },
            "action_result": { /* result details */ }
        }
        // More actions...
    ],
    "action_type_2": [
        // Similar structure for different action types
    ]
    // More action types...
}
```

### Running Rule Learning

Use the provided script to perform rule learning on your trajectory data. Replace `"/path/to/buffer.json"` with the path to your JSON file containing trajectories.

```bash
python run_rulelearning.py \
    --model_name gpt-4 \
    --temperature 1 \
    --buffer /path/to/buffer.json
```


## Future Releases

The complete source code and additional features will be made publicly available upon the acceptance of our accompanying research paper. Stay tuned for updates!


