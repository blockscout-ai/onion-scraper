#!/usr/bin/env python3
"""
Script to consolidate all unique rows from all discovered_onions CSV files
into a single master file with comprehensive deduplication.
"""

import csv
import os
import glob
from urllib.parse import urlparse
import re
from datetime import datetime
from collections import defaultdict

def extract_clean_onion(domain):
    """Extract clean onion domain from URL."""
    # Try the strict 56-character format first
    match = re.search(r"([a-z2-7]{56})\.onion", domain)
    if match:
        return match.group(0)
    
    # Try shorter onion addresses (some are 16 characters)
    match = re.search(r"([a-z2-7]{16})\.onion", domain)
    if match:
        return match.group(0)
    
    # Try any onion address format
    match = re.search(r"([a-z2-7]{10,56})\.onion", domain)
    if match:
        return match.group(0)
    
    return None

def consolidate_onion_files():
    """Consolidate all discovered_onions CSV files into a single master file."""
    print("🔗 Onion Discovery Consolidator")
    print("=" * 60)
    
    # Find all discovery CSV files (current and archived)
    current_files = glob.glob("discovered_onions_*.csv")
    archived_files = glob.glob("data/archives/discovered_onions_archive/discovered_onions_*.csv")
    
    csv_files = current_files + archived_files
    
    if not csv_files:
        print("❌ No discovered_onions CSV files found")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    print("   Current files:")
    for f in sorted(current_files):
        print(f"     - {f}")
    print("   Archived files:")
    for f in sorted(archived_files):
        print(f"     - {f}")
    
    print("\n" + "=" * 60)
    
    # Track all onions and their metadata
    onion_data = {}  # {clean_onion: {url, source, depth, timestamp, title, file_count}}
    file_stats = {}  # {filename: {total, unique, duplicates}}
    
    # Process each file
    for filename in csv_files:
        print(f"📖 Processing {filename}...")
        
        file_stats[filename] = {
            'total': 0,
            'unique': 0,
            'duplicates': 0
        }
        
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header
                
                # Check if file has header or starts with data
                first_row = next(reader, None)
                if not first_row:
                    print(f"⚠️  Skipping {filename} - empty file")
                    continue
                
                # If first row looks like a URL (starts with http), treat as data row
                # Otherwise, assume it's a header and get the next row
                if first_row[0].startswith('http'):
                    # No header, first row is data
                    url_index = 0
                    # Process the first row
                    file_stats[filename]['total'] += 1
                    onion_url = first_row[url_index]
                    parsed_url = urlparse(onion_url)
                    
                    if parsed_url.hostname:
                        clean_onion = extract_clean_onion(parsed_url.hostname)
                        
                        if clean_onion:
                            # Extract other columns if available
                            source = first_row[1] if len(first_row) > 1 else ""
                            depth = first_row[2] if len(first_row) > 2 else "0"
                            timestamp = first_row[3] if len(first_row) > 3 else datetime.utcnow().isoformat()
                            title = first_row[4] if len(first_row) > 4 else ""
                            
                            if clean_onion not in onion_data:
                                # New onion - add it
                                onion_data[clean_onion] = {
                                    'url': onion_url,
                                    'source': source,
                                    'depth': depth,
                                    'timestamp': timestamp,
                                    'title': title,
                                    'file_count': 1,
                                    'files': [filename]
                                }
                                file_stats[filename]['unique'] += 1
                            else:
                                # Duplicate onion - update metadata
                                existing = onion_data[clean_onion]
                                existing['file_count'] += 1
                                existing['files'].append(filename)
                                
                                # Keep the earliest timestamp
                                try:
                                    existing_time = datetime.fromisoformat(existing['timestamp'].replace('Z', '+00:00'))
                                    new_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    if new_time < existing_time:
                                        existing['timestamp'] = timestamp
                                except:
                                    pass  # Keep existing timestamp if parsing fails
                                
                                file_stats[filename]['duplicates'] += 1
                        else:
                            print(f"⚠️  Invalid onion format in {filename}: {onion_url}")
                    else:
                        print(f"⚠️  Invalid URL in {filename}: {onion_url}")
                else:
                    # Has header, find onion_url column
                    try:
                        url_index = first_row.index('onion_url')
                    except ValueError:
                        print(f"⚠️  Skipping {filename} - missing 'onion_url' column in header")
                        continue
                
                # Process remaining rows
                for row in reader:
                    file_stats[filename]['total'] += 1
                    
                    if len(row) > url_index:
                        onion_url = row[url_index]
                        parsed_url = urlparse(onion_url)
                        
                        if parsed_url.hostname:
                            clean_onion = extract_clean_onion(parsed_url.hostname)
                            
                            if clean_onion:
                                # Extract other columns if available
                                source = row[1] if len(row) > 1 else ""
                                depth = row[2] if len(row) > 2 else "0"
                                timestamp = row[3] if len(row) > 3 else datetime.utcnow().isoformat()
                                title = row[4] if len(row) > 4 else ""
                                
                                if clean_onion not in onion_data:
                                    # New onion - add it
                                    onion_data[clean_onion] = {
                                        'url': onion_url,
                                        'source': source,
                                        'depth': depth,
                                        'timestamp': timestamp,
                                        'title': title,
                                        'file_count': 1,
                                        'files': [filename]
                                    }
                                    file_stats[filename]['unique'] += 1
                                else:
                                    # Duplicate onion - update metadata
                                    existing = onion_data[clean_onion]
                                    existing['file_count'] += 1
                                    existing['files'].append(filename)
                                    
                                    # Keep the earliest timestamp
                                    try:
                                        existing_time = datetime.fromisoformat(existing['timestamp'].replace('Z', '+00:00'))
                                        new_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                        if new_time < existing_time:
                                            existing['timestamp'] = timestamp
                                    except:
                                        pass  # Keep existing timestamp if parsing fails
                                    
                                    file_stats[filename]['duplicates'] += 1
                            else:
                                print(f"⚠️  Invalid onion format in {filename}: {onion_url}")
                        else:
                            print(f"⚠️  Invalid URL in {filename}: {onion_url}")
                    else:
                        print(f"⚠️  Malformed row in {filename}: {row}")
                        
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
    
    # Print file statistics
    print("\n📊 File Statistics:")
    print("-" * 60)
    total_files_processed = 0
    total_rows_processed = 0
    total_unique_found = 0
    total_duplicates_found = 0
    
    for filename, stats in file_stats.items():
        print(f"📄 {filename}:")
        print(f"   Total rows: {stats['total']}")
        print(f"   Unique onions: {stats['unique']}")
        print(f"   Duplicates: {stats['duplicates']}")
        total_files_processed += 1
        total_rows_processed += stats['total']
        total_unique_found += stats['unique']
        total_duplicates_found += stats['duplicates']
    
    print("\n" + "=" * 60)
    print("📈 CONSOLIDATION SUMMARY:")
    print(f"   Files processed: {total_files_processed}")
    print(f"   Total rows processed: {total_rows_processed}")
    print(f"   Total unique onions found: {len(onion_data)}")
    print(f"   Total duplicates removed: {total_duplicates_found}")
    if total_rows_processed > 0:
        print(f"   Deduplication rate: {(total_duplicates_found / total_rows_processed * 100):.1f}%")
    else:
        print(f"   Deduplication rate: N/A (no rows processed)")
    
    # Create consolidated file
    consolidated_filename = f"consolidated_onions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    print(f"\n💾 Creating consolidated file: {consolidated_filename}")
    
    try:
        with open(consolidated_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'onion_url', 'source', 'depth', 'timestamp', 'title', 
                'discovery_count', 'source_files'
            ])
            
            # Write consolidated data
            for clean_onion, data in sorted(onion_data.items()):
                writer.writerow([
                    data['url'],
                    data['source'],
                    data['depth'],
                    data['timestamp'],
                    data['title'],
                    data['file_count'],
                    ';'.join(data['files'])
                ])
        
        print(f"✅ Successfully created {consolidated_filename}")
        print(f"📊 Consolidated file contains {len(onion_data)} unique onions")
        
        # Show some examples of onions found in multiple files
        multi_file_onions = {k: v for k, v in onion_data.items() if v['file_count'] > 1}
        if multi_file_onions:
            print(f"\n🔍 Found {len(multi_file_onions)} onions in multiple files:")
            for clean_onion, data in sorted(multi_file_onions.items(), key=lambda x: x[1]['file_count'], reverse=True)[:10]:
                print(f"   {clean_onion} (found in {data['file_count']} files)")
        
        return consolidated_filename
        
    except Exception as e:
        print(f"❌ Error creating consolidated file: {e}")
        return None

def analyze_consolidated_file(filename):
    """Analyze the consolidated file for insights."""
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found")
        return
    
    print(f"\n📊 Analyzing consolidated file: {filename}")
    print("-" * 60)
    
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            total_rows = 0
            source_stats = defaultdict(int)
            depth_stats = defaultdict(int)
            discovery_count_stats = defaultdict(int)
            
            for row in reader:
                total_rows += 1
                
                if len(row) >= 7:
                    source = row[1]
                    depth = row[2]
                    discovery_count = int(row[5]) if row[5].isdigit() else 1
                    
                    source_stats[source] += 1
                    depth_stats[depth] += 1
                    discovery_count_stats[discovery_count] += 1
            
            print(f"📈 Total unique onions: {total_rows}")
            
            print(f"\n🔍 Top 10 sources:")
            for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   {source}: {count} onions")
            
            print(f"\n📊 Depth distribution:")
            for depth, count in sorted(depth_stats.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                print(f"   Depth {depth}: {count} onions")
            
            print(f"\n🔄 Discovery frequency:")
            for count, onions in sorted(discovery_count_stats.items()):
                print(f"   Found in {count} file(s): {onions} onions")
                
    except Exception as e:
        print(f"❌ Error analyzing consolidated file: {e}")

def main():
    """Main function to consolidate onion files."""
    # Consolidate all files
    consolidated_file = consolidate_onion_files()
    
    if consolidated_file:
        # Analyze the consolidated file
        analyze_consolidated_file(consolidated_file)
        
        print(f"\n🎉 Consolidation complete!")
        print(f"📁 Master file: {consolidated_file}")
        print(f"💡 You can now use this consolidated file as your master onion database")

if __name__ == "__main__":
    main() 