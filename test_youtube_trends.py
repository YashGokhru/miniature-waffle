"""
Unit tests for YouTube Trends Scraper

These tests use mocked API responses and do not require real API keys or network calls.
"""

import pytest
import json
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from youtube_trends import (
    YouTubeTrendsScraper,
    YouTubeTrendsScraperError,
    parse_args,
    main
)


class TestYouTubeTrendsScraper:
    """Tests for YouTubeTrendsScraper class"""
    
    def test_init_with_valid_api_key(self):
        """Test initialization with a valid API key"""
        with patch('youtube_trends.build') as mock_build:
            scraper = YouTubeTrendsScraper('test-api-key')
            assert scraper.api_key == 'test-api-key'
            mock_build.assert_called_once_with('youtube', 'v3', developerKey='test-api-key')
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error"""
        with pytest.raises(YouTubeTrendsScraperError, match="YouTube API key is required"):
            YouTubeTrendsScraper('')
    
    def test_search_videos_success(self):
        """Test successful video search"""
        with patch('youtube_trends.build') as mock_build:
            # Mock the YouTube API response
            mock_youtube = MagicMock()
            mock_build.return_value = mock_youtube
            
            mock_search_response = {
                'items': [
                    {'id': {'videoId': 'video1'}},
                    {'id': {'videoId': 'video2'}},
                    {'id': {'videoId': 'video3'}}
                ]
            }
            
            mock_youtube.search().list().execute.return_value = mock_search_response
            
            scraper = YouTubeTrendsScraper('test-api-key')
            video_ids = scraper.search_videos('test query', region='US', max_results=25)
            
            assert len(video_ids) == 3
            assert video_ids == ['video1', 'video2', 'video3']
            
            # Verify the API was called with correct parameters
            call_kwargs = mock_youtube.search().list.call_args[1]
            assert call_kwargs['q'] == 'test query'
            assert call_kwargs['regionCode'] == 'US'
            assert call_kwargs['maxResults'] == 25
            assert call_kwargs['type'] == 'video'
    
    def test_search_videos_with_published_after(self):
        """Test video search with publishedAfter parameter"""
        with patch('youtube_trends.build') as mock_build:
            mock_youtube = MagicMock()
            mock_build.return_value = mock_youtube
            
            mock_search_response = {'items': [{'id': {'videoId': 'video1'}}]}
            mock_youtube.search().list().execute.return_value = mock_search_response
            
            scraper = YouTubeTrendsScraper('test-api-key')
            published_after = '2024-01-01T00:00:00Z'
            scraper.search_videos('test', published_after=published_after)
            
            call_kwargs = mock_youtube.search().list.call_args[1]
            assert call_kwargs['publishedAfter'] == published_after
    
    def test_get_video_details_success(self):
        """Test successful video details retrieval"""
        with patch('youtube_trends.build') as mock_build:
            mock_youtube = MagicMock()
            mock_build.return_value = mock_youtube
            
            mock_videos_response = {
                'items': [
                    {
                        'id': 'video1',
                        'snippet': {
                            'title': 'Test Video 1',
                            'channelTitle': 'Test Channel 1',
                            'publishedAt': '2024-01-01T00:00:00Z'
                        },
                        'statistics': {
                            'viewCount': '1000',
                            'likeCount': '100',
                            'commentCount': '10'
                        }
                    },
                    {
                        'id': 'video2',
                        'snippet': {
                            'title': 'Test Video 2',
                            'channelTitle': 'Test Channel 2',
                            'publishedAt': '2024-01-02T00:00:00Z'
                        },
                        'statistics': {
                            'viewCount': '2000',
                            'likeCount': '200',
                            'commentCount': '20'
                        }
                    }
                ]
            }
            
            mock_youtube.videos().list().execute.return_value = mock_videos_response
            
            scraper = YouTubeTrendsScraper('test-api-key')
            videos = scraper.get_video_details(['video1', 'video2'])
            
            assert len(videos) == 2
            assert videos[0]['id'] == 'video1'
            assert videos[0]['title'] == 'Test Video 1'
            assert videos[0]['channelTitle'] == 'Test Channel 1'
            assert videos[0]['viewCount'] == 1000
            assert videos[0]['likeCount'] == 100
            assert videos[0]['commentCount'] == 10
            assert videos[0]['url'] == 'https://www.youtube.com/watch?v=video1'
            
            assert videos[1]['id'] == 'video2'
            assert videos[1]['viewCount'] == 2000
    
    def test_get_video_details_empty_list(self):
        """Test video details with empty video ID list"""
        with patch('youtube_trends.build') as mock_build:
            scraper = YouTubeTrendsScraper('test-api-key')
            videos = scraper.get_video_details([])
            assert videos == []
    
    def test_get_video_details_missing_statistics(self):
        """Test video details handles missing statistics gracefully"""
        with patch('youtube_trends.build') as mock_build:
            mock_youtube = MagicMock()
            mock_build.return_value = mock_youtube
            
            mock_videos_response = {
                'items': [
                    {
                        'id': 'video1',
                        'snippet': {
                            'title': 'Test Video',
                            'channelTitle': 'Test Channel',
                            'publishedAt': '2024-01-01T00:00:00Z'
                        },
                        'statistics': {}  # Missing statistics
                    }
                ]
            }
            
            mock_youtube.videos().list().execute.return_value = mock_videos_response
            
            scraper = YouTubeTrendsScraper('test-api-key')
            videos = scraper.get_video_details(['video1'])
            
            assert len(videos) == 1
            assert videos[0]['viewCount'] == 0
            assert videos[0]['likeCount'] == 0
            assert videos[0]['commentCount'] == 0
    
    def test_get_trends_sorts_by_view_count(self):
        """Test that get_trends sorts videos by view count"""
        with patch('youtube_trends.build') as mock_build:
            mock_youtube = MagicMock()
            mock_build.return_value = mock_youtube
            
            # Mock search response
            mock_search_response = {
                'items': [
                    {'id': {'videoId': 'video1'}},
                    {'id': {'videoId': 'video2'}},
                    {'id': {'videoId': 'video3'}}
                ]
            }
            mock_youtube.search().list().execute.return_value = mock_search_response
            
            # Mock videos response with different view counts
            mock_videos_response = {
                'items': [
                    {
                        'id': 'video1',
                        'snippet': {
                            'title': 'Video 1',
                            'channelTitle': 'Channel 1',
                            'publishedAt': '2024-01-01T00:00:00Z'
                        },
                        'statistics': {'viewCount': '500', 'likeCount': '10', 'commentCount': '5'}
                    },
                    {
                        'id': 'video2',
                        'snippet': {
                            'title': 'Video 2',
                            'channelTitle': 'Channel 2',
                            'publishedAt': '2024-01-02T00:00:00Z'
                        },
                        'statistics': {'viewCount': '2000', 'likeCount': '20', 'commentCount': '10'}
                    },
                    {
                        'id': 'video3',
                        'snippet': {
                            'title': 'Video 3',
                            'channelTitle': 'Channel 3',
                            'publishedAt': '2024-01-03T00:00:00Z'
                        },
                        'statistics': {'viewCount': '1000', 'likeCount': '15', 'commentCount': '7'}
                    }
                ]
            }
            mock_youtube.videos().list().execute.return_value = mock_videos_response
            
            scraper = YouTubeTrendsScraper('test-api-key')
            videos = scraper.get_trends('test query')
            
            # Verify sorting by view count (descending)
            assert len(videos) == 3
            assert videos[0]['id'] == 'video2'
            assert videos[0]['viewCount'] == 2000
            assert videos[1]['id'] == 'video3'
            assert videos[1]['viewCount'] == 1000
            assert videos[2]['id'] == 'video1'
            assert videos[2]['viewCount'] == 500


class TestArgumentParsing:
    """Tests for command-line argument parsing"""
    
    def test_parse_args_basic_query(self):
        """Test parsing basic query argument"""
        test_args = ['--query', 'AI']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.queries == ['AI']
            assert args.region == 'US'
            assert args.max_results == 25
            assert args.order == 'relevance'
    
    def test_parse_args_multiple_queries(self):
        """Test parsing multiple query arguments"""
        test_args = ['--query', 'AI', '--query', 'ML']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.queries == ['AI', 'ML']
    
    def test_parse_args_with_region(self):
        """Test parsing with custom region"""
        test_args = ['--query', 'cricket', '--region', 'IN']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.region == 'IN'
    
    def test_parse_args_with_max_results(self):
        """Test parsing with max results"""
        test_args = ['--query', 'test', '--max-results', '50']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.max_results == 50
    
    def test_parse_args_with_days(self):
        """Test parsing with days parameter"""
        test_args = ['--query', 'test', '--days', '7']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.days == 7
    
    def test_parse_args_with_published_after(self):
        """Test parsing with published-after parameter"""
        test_args = ['--query', 'test', '--published-after', '2024-01-01T00:00:00Z']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.published_after == '2024-01-01T00:00:00Z'
    
    def test_parse_args_with_order(self):
        """Test parsing with order parameter"""
        test_args = ['--query', 'test', '--order', 'viewCount']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.order == 'viewCount'
    
    def test_parse_args_with_output_file(self):
        """Test parsing with output file parameter"""
        test_args = ['--query', 'test', '--out', 'results.json']
        with patch('sys.argv', ['youtube_trends.py'] + test_args):
            args = parse_args()
            assert args.output_file == 'results.json'


class TestMainFunction:
    """Tests for main CLI function"""
    
    def test_main_missing_api_key(self, capsys):
        """Test main exits when API key is missing"""
        test_args = ['youtube_trends.py', '--query', 'test']
        with patch('sys.argv', test_args):
            with patch.dict('os.environ', {}, clear=True):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert 'YOUTUBE_API_KEY' in captured.err
    
    def test_main_comma_separated_queries(self, capsys):
        """Test main handles comma-separated queries"""
        test_args = ['youtube_trends.py', '--query', 'AI,ML,Python']
        
        with patch('sys.argv', test_args):
            with patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test-key'}):
                with patch('youtube_trends.build') as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube
                    
                    # Mock empty responses
                    mock_youtube.search().list().execute.return_value = {'items': []}
                    mock_youtube.videos().list().execute.return_value = {'items': []}
                    
                    main()
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        
        # Should have 3 searches (one for each comma-separated query)
        assert len(output['searches']) == 3
        assert output['searches'][0]['query'] == 'AI'
        assert output['searches'][1]['query'] == 'ML'
        assert output['searches'][2]['query'] == 'Python'
    
    def test_main_with_days_parameter(self, capsys):
        """Test main correctly calculates published_after from days parameter"""
        test_args = ['youtube_trends.py', '--query', 'test', '--days', '7']
        
        with patch('sys.argv', test_args):
            with patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test-key'}):
                with patch('youtube_trends.build') as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube
                    
                    mock_youtube.search().list().execute.return_value = {'items': []}
                    mock_youtube.videos().list().execute.return_value = {'items': []}
                    
                    # Capture the datetime when test runs
                    before_time = datetime.utcnow() - timedelta(days=7)
                    
                    main()
                    
                    # Verify published_after was passed
                    call_kwargs = mock_youtube.search().list.call_args[1]
                    assert 'publishedAfter' in call_kwargs
                    
                    # Parse and verify it's approximately 7 days ago
                    published_after_str = call_kwargs['publishedAfter']
                    published_after_dt = datetime.strptime(published_after_str, '%Y-%m-%dT%H:%M:%SZ')
                    
                    # Should be within a few seconds of 7 days ago
                    time_diff = abs((published_after_dt - before_time).total_seconds())
                    assert time_diff < 5  # Allow 5 seconds tolerance
    
    def test_main_output_json_structure(self, capsys):
        """Test main produces correct JSON output structure"""
        test_args = ['youtube_trends.py', '--query', 'test']
        
        with patch('sys.argv', test_args):
            with patch.dict('os.environ', {'YOUTUBE_API_KEY': 'test-key'}):
                with patch('youtube_trends.build') as mock_build:
                    mock_youtube = MagicMock()
                    mock_build.return_value = mock_youtube
                    
                    # Mock search response
                    mock_youtube.search().list().execute.return_value = {
                        'items': [{'id': {'videoId': 'test-video-id'}}]
                    }
                    
                    # Mock video details response
                    mock_youtube.videos().list().execute.return_value = {
                        'items': [{
                            'id': 'test-video-id',
                            'snippet': {
                                'title': 'Test Video',
                                'channelTitle': 'Test Channel',
                                'publishedAt': '2024-01-01T00:00:00Z'
                            },
                            'statistics': {
                                'viewCount': '1000',
                                'likeCount': '100',
                                'commentCount': '10'
                            }
                        }]
                    }
                    
                    main()
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        
        # Verify top-level structure
        assert 'searches' in output
        assert 'metadata' in output
        
        # Verify metadata
        assert output['metadata']['queries'] == ['test']
        assert output['metadata']['region'] == 'US'
        assert output['metadata']['max_results_per_query'] == 25
        
        # Verify search result structure
        assert len(output['searches']) == 1
        search_result = output['searches'][0]
        
        assert search_result['query'] == 'test'
        assert search_result['region'] == 'US'
        assert 'generated_at' in search_result
        assert 'items' in search_result
        
        # Verify video item structure
        assert len(search_result['items']) == 1
        video = search_result['items'][0]
        
        required_fields = ['id', 'title', 'channelTitle', 'publishedAt', 'url', 'viewCount', 'likeCount', 'commentCount']
        for field in required_fields:
            assert field in video
        
        assert video['id'] == 'test-video-id'
        assert video['title'] == 'Test Video'
        assert video['viewCount'] == 1000
