proj_clean/directory_to_markdown.py
import argparse
import logging
from pathlib import Path
from typing import Set, Union

# Default directories to ignore
DEFAULT_IGNORE_DIRS = {'node_modules', '__pycache__', '.git', '.vscode', '.idea'}

def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def is_ignored(path: Path, ignore_dirs: Set[str]) -> bool:
    """
    Check if the path is inside any ignored directory.

    Args:
        path: The path to check.
        ignore_dirs: Set of directory names to ignore.

    Returns:
        bool: True if the path should be ignored, False otherwise.
    """
    for part in path.parts:
        if part in ignore_dirs:
            return True
    return False

def read_file_safely(file_path: Path, max_size_mb: int) -> str:
    """
    Read file contents safely, checking file size and encoding.

    Args:
        file_path: Path to the file to read.
        max_size_mb: Maximum file size in megabytes.

    Returns:
        str: The file content as a string.

    Raises:
        OSError: If file cannot be read due to size or encoding issues.
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    file_size = file_path.stat().st_size
    if file_size > max_size_bytes:
        raise OSError(f"File too large: {file_path} ({file_size} bytes > {max_size_bytes} bytes)")
    
    try:
        content = file_path.read_text(encoding='utf-8')
        return content
    except UnicodeDecodeError:
        logging.warning(f"Skipping file due to encoding issues: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise

def directory_to_markdown(
    directory_path: Union[str, Path],
    output_file: Union[str, Path],
    file_types: Set[str] = None,
    ignore_dirs: Set[str] = None,
    recursive: bool = True,
    max_file_size_mb: int = 10
) -> None:
    """
    Traverse directory, read selected files, and write their contents into a markdown file.

    Args:
        directory_path: Directory to traverse.
        output_file: Markdown file to generate.
        file_types: File extensions to include (e.g., {'.py', '.txt'}).
        ignore_dirs: Directory names to ignore.
        recursive: Whether to traverse subdirectories.
        max_file_size_mb: Maximum file size to process in megabytes.
    """
    if file_types is None:
        file_types = {'.py', '.txt', '.md', '.js', '.html', '.css', '.json', '.yaml', '.yml'}
    
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS
    
    directory_path = Path(directory_path)
    output_file = Path(output_file)
    
    if not directory_path.exists():
        raise ValueError(f"Directory does not exist: {directory_path}")
    
    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory_path}")
    
    logging.info(f"Starting directory traversal: {directory_path}")
    logging.info(f"Output file: {output_file}")
    logging.info(f"File types: {file_types}")
    logging.info(f"Ignored directories: {ignore_dirs}")
    logging.info(f"Recursive: {recursive}")
    logging.info(f"Max file size: {max_file_size_mb} MB")
    
    with output_file.open('w', encoding='utf-8') as md_file:
        md_file.write(f"# Directory Contents: {directory_path}\n\n")
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            if is_ignored(file_path, ignore_dirs):
                logging.debug(f"Ignoring file in excluded directory: {file_path}")
                continue
            
            if file_path.suffix not in file_types:
                logging.debug(f"Skipping file type: {file_path}")
                continue
            
            try:
                content = read_file_safely(file_path, max_file_size_mb)
                
                relative_path = file_path.relative_to(directory_path)
                md_file.write(f"## File: `{relative_path}`\n\n")
                md_file.write(f"```{file_path.suffix.lstrip('.')}\n")
                md_file.write(content)
                md_file.write("\n```\n\n")
                
                logging.info(f"Processed: {file_path}")
                
            except (OSError, UnicodeDecodeError) as e:
                logging.warning(f"Skipping file {file_path}: {e}")
            except Exception as e:
                logging.error(f"Unexpected error processing {file_path}: {e}")
    
    logging.info(f"Markdown file generated: {output_file}")

def main() -> None:
    """Main function to handle command line arguments and execute the conversion."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Convert directory contents to Markdown format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "directory",
        help="Directory path to traverse"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output.md",
        help="Output markdown file path"
    )
    
    parser.add_argument(
        "-t", "--types",
        nargs="+",
        default=['.py', '.txt', '.md', '.js', '.html', '.css', '.json', '.yaml', '.yml'],
        help="File extensions to include"
    )
    
    parser.add_argument(
        "-i", "--ignore",
        nargs="+",
        default=DEFAULT_IGNORE_DIRS,
        help="Directories to ignore"
    )
    
    parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Disable recursive directory traversal"
    )
    
    parser.add_argument(
        "--max-size",
        type=int,
        default=10,
        help="Maximum file size in megabytes"
    )
    
    args = parser.parse_args()
    
    try:
        directory_to_markdown(
            directory_path=args.directory,
            output_file=args.output,
            file_types=set(args.types),
            ignore_dirs=set(args.ignore),
            recursive=args.recursive,
            max_file_size_mb=args.max_size
        )
    except Exception as e:
        logging.error(f"Failed to generate markdown: {e}")
        exit(1)

if __name__ == "__main__":
    main()