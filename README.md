# YouTube Trends Scraper

A command-line tool to discover trending YouTube videos for given keywords using the YouTube Data API v3.

## Features

- 🔍 Search for trending videos by keyword
- 🌍 Support for different regions/countries
- 📊 Fetch detailed statistics (views, likes, comments)
- 📅 Filter by publication date
- 💾 Export results as JSON
- 🤖 GitHub Actions workflow for automated daily scraping
- ✅ Comprehensive test suite with mocked API calls

## What are "Trends"?

This tool defines "trends" as videos retrieved from YouTube's search API for given keywords, enriched with engagement statistics (views, likes, comments), and sorted by view count. The search results are based on YouTube's relevance algorithm (or other ordering like `viewCount`, `date`, etc.), giving you a snapshot of what content is currently popular for your chosen keywords.

## Requirements

- Python 3.7+
- YouTube Data API v3 key (free from Google Cloud Console)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/YashGokhru/miniature-waffle.git
   cd miniature-waffle
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Get a YouTube Data API v3 key:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (or select an existing one)
   - Enable the YouTube Data API v3
   - Create credentials (API Key)
   - Copy your API key

4. Set your API key as an environment variable:
   ```bash
   export YOUTUBE_API_KEY='your-api-key-here'
   ```

## Usage

### Basic Usage

Search for trending videos about AI:
```bash
python youtube_trends.py --query "AI"
```

### Multiple Keywords

Search for multiple keywords (multiple --query flags):
```bash
python youtube_trends.py --query "AI" --query "machine learning" --query "python"
```

Or use comma-separated values:
```bash
python youtube_trends.py --query "AI,machine learning,python"
```

### Region-Specific Search

Search with a specific region code:
```bash
python youtube_trends.py --query "cricket" --region IN
```

Common region codes: `US` (United States), `IN` (India), `GB` (United Kingdom), `CA` (Canada), `AU` (Australia)

### Limit Results

Get more or fewer results per query:
```bash
python youtube_trends.py --query "technology" --max-results 50
```

### Filter by Date

Get videos from the last 7 days:
```bash
python youtube_trends.py --query "news" --days 7
```

Or specify an exact date:
```bash
python youtube_trends.py --query "tutorial" --published-after 2024-01-01T00:00:00Z
```

### Change Sort Order

Order results by different criteria:
```bash
python youtube_trends.py --query "music" --order viewCount
```

Available orders: `relevance` (default), `date`, `rating`, `viewCount`, `title`

### Save to File

Save results to a JSON file instead of stdout:
```bash
python youtube_trends.py --query "science" --out results.json
```

### Complete Example

```bash
python youtube_trends.py \
  --query "python programming,web development" \
  --region US \
  --max-results 30 \
  --days 14 \
  --order viewCount \
  --out trending_programming.json
```

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Keyword to search (can be specified multiple times or comma-separated) | Required |
| `--region` | `-r` | Region code for search | `US` |
| `--max-results` | `-m` | Maximum number of results per query | `25` |
| `--days` | `-d` | Limit to videos published in last N days | None |
| `--published-after` | `-p` | Limit to videos published after this date (RFC 3339 format) | None |
| `--order` | `-o` | Order of search results (`relevance`, `date`, `rating`, `viewCount`, `title`) | `relevance` |
| `--out` | `-f` | Output JSON file path | stdout |

## Output Format

The tool outputs JSON with the following structure (see `example_output.json` for a complete example):

```json
{
  "searches": [
    {
      "query": "AI",
      "region": "US",
      "generated_at": "2024-02-17T12:00:00.000000Z",
      "items": [
        {
          "id": "dQw4w9WgXcQ",
          "title": "Video Title",
          "channelTitle": "Channel Name",
          "publishedAt": "2024-02-10T10:00:00Z",
          "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
          "viewCount": 1000000,
          "likeCount": 50000,
          "commentCount": 2500
        }
      ]
    }
  ],
  "metadata": {
    "generated_at": "2024-02-17T12:00:00.000000Z",
    "queries": ["AI"],
    "region": "US",
    "max_results_per_query": 25,
    "published_after": null,
    "order": "relevance"
  }
}
```

## GitHub Actions Workflow

The repository includes a GitHub Actions workflow that automatically scrapes trends daily.

### Setup

1. Add your YouTube API key as a repository secret:
   - Go to your repository on GitHub
   - Navigate to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `YOUTUBE_API_KEY`
   - Value: Your YouTube Data API v3 key
   - Click **Add secret**

2. The workflow is already configured in `.github/workflows/youtube-trends.yml`

### Configuration

Edit the workflow file to customize default queries and schedule:

**Default Queries** (used for scheduled runs):
```yaml
env:
  DEFAULT_QUERIES: 'AI,technology,programming,science'
  DEFAULT_REGION: 'US'
  DEFAULT_MAX_RESULTS: '25'
  DEFAULT_DAYS: '7'
```

**Schedule** (currently daily at midnight UTC):
```yaml
schedule:
  - cron: '0 0 * * *'  # Daily at 00:00 UTC
```

Change to run twice daily:
```yaml
schedule:
  - cron: '0 0,12 * * *'  # Daily at 00:00 and 12:00 UTC
```

### Manual Trigger

You can manually trigger the workflow with custom parameters:

1. Go to **Actions** tab in your repository
2. Select **YouTube Trends Scraper** workflow
3. Click **Run workflow**
4. Enter custom parameters:
   - **queries**: Comma-separated keywords (e.g., `AI,blockchain,gaming`)
   - **region**: Region code (e.g., `US`, `IN`, `GB`)
   - **max_results**: Number per query (e.g., `50`)
   - **days**: Limit to last N days (e.g., `14`)
5. Click **Run workflow**

### Accessing Results

After the workflow runs:

1. Go to the **Actions** tab
2. Click on the completed workflow run
3. Scroll down to **Artifacts**
4. Download the `youtube-trends-<region>-<run-number>` artifact
5. Extract the ZIP to get the `youtube_trends_output.json` file

Artifacts are retained for 90 days by default.

## Development

### Running Tests

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Run the test suite:
```bash
pytest test_youtube_trends.py -v
```

Run tests with coverage:
```bash
pytest test_youtube_trends.py --cov=youtube_trends --cov-report=html
```

All tests use mocked API responses and do not require a real API key or network connection.

### Test Coverage

The test suite includes:
- ✅ API client initialization and error handling
- ✅ Video search with various parameters
- ✅ Video details retrieval and parsing
- ✅ View count sorting for "trending" effect
- ✅ Command-line argument parsing
- ✅ Main function integration with all features
- ✅ JSON output structure validation
- ✅ Date filtering and calculation
- ✅ Error handling for missing API keys

## API Rate Limits

The YouTube Data API v3 has quota limits. Each request consumes quota:
- `search.list`: 100 units
- `videos.list`: 1 unit

Default daily quota: 10,000 units

For the default settings (25 results per query), you can run approximately:
- Single query: ~100 times per day
- Multiple queries: Divide by number of queries

Monitor your quota in the [Google Cloud Console](https://console.cloud.google.com/).

## Troubleshooting

**Error: YOUTUBE_API_KEY environment variable is not set**
- Solution: Export your API key: `export YOUTUBE_API_KEY='your-key'`

**Error: YouTube API error during search**
- Check your API key is valid
- Verify the YouTube Data API v3 is enabled in your Google Cloud project
- Check you haven't exceeded your quota limits

**No results returned**
- Try different keywords or less restrictive date filters
- Some regions may have less content for specific queries

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue in the GitHub repository.
