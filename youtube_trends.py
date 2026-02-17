#!/usr/bin/env python3
"""
YouTube Trends Scraper CLI

A command-line tool to discover trending YouTube videos for given keywords using the YouTube Data API v3.

"Trends" Definition:
--------------------
Videos are retrieved using the YouTube Data API search.list endpoint ordered by relevance,
filtered by publishedAfter date (if specified), and enriched with statistics (viewCount, likeCount, commentCount).
The results represent videos currently trending for the given keywords based on YouTube's search algorithm
combined with engagement metrics.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeTrendsScraperError(Exception):
    """Base exception for YouTube Trends Scraper"""
    pass


class YouTubeTrendsScraper:
    """Client for fetching trending YouTube videos by keyword using YouTube Data API v3"""
    
    def __init__(self, api_key: str):
        """
        Initialize the YouTube Trends Scraper.
        
        Args:
            api_key: YouTube Data API v3 key
        """
        if not api_key:
            raise YouTubeTrendsScraperError("YouTube API key is required")
        
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_videos(
        self,
        query: str,
        region: str = 'US',
        max_results: int = 25,
        published_after: Optional[str] = None,
        order: str = 'relevance'
    ) -> List[str]:
        """
        Search for videos matching the query.
        
        Args:
            query: Search query/keyword
            region: Region code (default: US)
            max_results: Maximum number of results (default: 25)
            published_after: RFC 3339 formatted date-time (e.g., '2024-01-01T00:00:00Z')
            order: Order parameter (relevance, date, rating, viewCount, etc.)
        
        Returns:
            List of video IDs
        """
        try:
            search_params = {
                'part': 'id',
                'q': query,
                'type': 'video',
                'regionCode': region,
                'maxResults': max_results,
                'order': order
            }
            
            if published_after:
                search_params['publishedAfter'] = published_after
            
            search_response = self.youtube.search().list(**search_params).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            return video_ids
        
        except HttpError as e:
            raise YouTubeTrendsScraperError(f"YouTube API error during search: {e}")
        except Exception as e:
            raise YouTubeTrendsScraperError(f"Error during video search: {e}")
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed statistics and metadata for given video IDs.
        
        Args:
            video_ids: List of YouTube video IDs
        
        Returns:
            List of video details with statistics
        """
        if not video_ids:
            return []
        
        try:
            videos_response = self.youtube.videos().list(
                part='snippet,statistics',
                id=','.join(video_ids)
            ).execute()
            
            videos = []
            for item in videos_response.get('items', []):
                video_id = item['id']
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                
                video_data = {
                    'id': video_id,
                    'title': snippet.get('title', ''),
                    'channelTitle': snippet.get('channelTitle', ''),
                    'publishedAt': snippet.get('publishedAt', ''),
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'viewCount': int(statistics.get('viewCount', 0)),
                    'likeCount': int(statistics.get('likeCount', 0)),
                    'commentCount': int(statistics.get('commentCount', 0))
                }
                videos.append(video_data)
            
            return videos
        
        except HttpError as e:
            raise YouTubeTrendsScraperError(f"YouTube API error fetching video details: {e}")
        except Exception as e:
            raise YouTubeTrendsScraperError(f"Error fetching video details: {e}")
    
    def get_trends(
        self,
        query: str,
        region: str = 'US',
        max_results: int = 25,
        published_after: Optional[str] = None,
        order: str = 'relevance'
    ) -> List[Dict[str, Any]]:
        """
        Get trending videos for a given query.
        
        Args:
            query: Search query/keyword
            region: Region code (default: US)
            max_results: Maximum number of results (default: 25)
            published_after: RFC 3339 formatted date-time
            order: Order parameter
        
        Returns:
            List of video details sorted by view count
        """
        video_ids = self.search_videos(query, region, max_results, published_after, order)
        videos = self.get_video_details(video_ids)
        
        # Sort by view count descending for "trending" effect
        videos.sort(key=lambda x: x['viewCount'], reverse=True)
        
        return videos


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='YouTube Trends Scraper - Find trending videos by keyword using YouTube Data API v3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "AI" --query "machine learning"
  %(prog)s --query "cricket,football" --region IN --max-results 50
  %(prog)s --query "python" --days 7 --out trends.json
  %(prog)s --query "technology" --published-after 2024-01-01T00:00:00Z

Environment Variables:
  YOUTUBE_API_KEY    YouTube Data API v3 key (required)
        """
    )
    
    parser.add_argument(
        '--query', '-q',
        action='append',
        dest='queries',
        required=True,
        help='Keyword query to search (can be specified multiple times or comma-separated)'
    )
    
    parser.add_argument(
        '--region', '-r',
        default='US',
        help='Region code for search (default: US)'
    )
    
    parser.add_argument(
        '--max-results', '-m',
        type=int,
        default=25,
        help='Maximum number of results per query (default: 25)'
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        help='Limit results to videos published in the last N days'
    )
    
    parser.add_argument(
        '--published-after', '-p',
        help='Limit results to videos published after this date (RFC 3339 format: YYYY-MM-DDTHH:MM:SSZ)'
    )
    
    parser.add_argument(
        '--order', '-o',
        default='relevance',
        choices=['relevance', 'date', 'rating', 'viewCount', 'title'],
        help='Order of search results (default: relevance)'
    )
    
    parser.add_argument(
        '--out', '-f',
        dest='output_file',
        help='Output JSON file path (default: stdout)'
    )
    
    return parser.parse_args()


def main():
    """Main CLI entry point"""
    args = parse_args()
    
    # Get API key from environment
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)
    
    # Parse queries (handle comma-separated values)
    queries = []
    for query_arg in args.queries:
        queries.extend([q.strip() for q in query_arg.split(',') if q.strip()])
    
    if not queries:
        print("Error: No valid queries provided", file=sys.stderr)
        sys.exit(1)
    
    # Calculate published_after if --days is specified
    published_after = args.published_after
    if args.days:
        days_ago = datetime.utcnow() - timedelta(days=args.days)
        published_after = days_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Initialize scraper
    try:
        scraper = YouTubeTrendsScraper(api_key)
    except YouTubeTrendsScraperError as e:
        print(f"Error initializing scraper: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fetch trends for each query
    results = []
    for query in queries:
        try:
            videos = scraper.get_trends(
                query=query,
                region=args.region,
                max_results=args.max_results,
                published_after=published_after,
                order=args.order
            )
            
            result = {
                'query': query,
                'region': args.region,
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'items': videos
            }
            results.append(result)
        
        except YouTubeTrendsScraperError as e:
            print(f"Error fetching trends for query '{query}': {e}", file=sys.stderr)
            # Continue with other queries
    
    # Output results
    output_data = {
        'searches': results,
        'metadata': {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'queries': queries,
            'region': args.region,
            'max_results_per_query': args.max_results,
            'published_after': published_after,
            'order': args.order
        }
    }
    
    output_json = json.dumps(output_data, indent=2)
    
    if args.output_file:
        try:
            with open(args.output_file, 'w') as f:
                f.write(output_json)
            print(f"Results written to {args.output_file}", file=sys.stderr)
        except IOError as e:
            print(f"Error writing to file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_json)


if __name__ == '__main__':
    main()
