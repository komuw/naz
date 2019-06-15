import linecache
import tracemalloc


def display_top_allocators(snapshot, key_type="lineno", limit=15):
    """
    displays the top N offenders by memory allocation.

    Usage:
        import wiji

        tracemalloc.start(25)
        # then run your long running code that you suspect to have a leak
        snapshot = tracemalloc.take_snapshot()
        wiji.utils.display_top_allocators(snapshot)

    see: https://github.com/komuw/wiji/issues/71
    for an actual usage of this function to debug a memory leak in real life.
    """
    snapshot = snapshot.filter_traces(
        (
            # exclude traces of this modules
            # TODO: add filters to remove all python stdlib
            tracemalloc.Filter(
                False, filename_pattern="<frozen importlib._bootstrap>"
            ),  # <Frame filename='<frozen importlib._bootstrap_external>' lineno=525>,
            tracemalloc.Filter(False, filename_pattern="<frozen importlib._bootstrap_external>"),
            tracemalloc.Filter(False, filename_pattern="<unknown>"),
            tracemalloc.Filter(False, filename_pattern="*json/encoder*"),
            tracemalloc.Filter(False, filename_pattern="*json/decoder*"),
            # import fnmatch
            # fnmatch.fnmatch('/lib/python3.7/json/encoder.py', '*json/encoder*')
            # see https://pymotw.com/3/fnmatch/
            #
            tracemalloc.Filter(False, filename_pattern="*tracemalloc.py"),
            tracemalloc.Filter(False, filename_pattern="*linecache.py"),
            tracemalloc.Filter(False, filename_pattern="*stringprep.py"),
            tracemalloc.Filter(False, filename_pattern="*threading.py"),
            tracemalloc.Filter(False, filename_pattern="*traceback.py"),
            tracemalloc.Filter(False, filename_pattern="*urllib/request*"),
        )
    )
    top_stats = snapshot.statistics(key_type)
    total = sum(stat.size for stat in top_stats)
    total_allocated_size = total / 1024

    print("Top {limit} lines".format(limit=limit))
    print(
        "total_allocated_size: {total_allocated_size:.1f}KiB".format(
            total_allocated_size=total_allocated_size
        )
    )

    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        # filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        filename = frame.filename
        lineno = frame.lineno
        stat_size = stat.size / 1024
        stat_count = stat.count
        offending_line = linecache.getline(filename, lineno).strip()

        print(
            "index:#{index}: file:{filename}:{lineno} stat_size:{stat_size:.1f}KiB stat_count:{stat_count}".format(
                index=index,
                filename=filename,
                lineno=lineno,
                stat_size=stat_size,
                stat_count=stat_count,
            )
        )
        if offending_line:
            print("\t offending_line: {offending_line}".format(offending_line=offending_line))

    # other offenders outside top X offenders
    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        combined_stat_size = size / 1024
        print(
            "num_other_offenders:{num_other_offenders} combined_stat_size:{combined_stat_size:.1f}KiB".format(
                num_other_offenders=len(other), combined_stat_size=combined_stat_size
            )
        )
