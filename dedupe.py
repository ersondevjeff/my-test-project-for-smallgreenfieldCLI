def dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main():
    sample = [1, 2, 3, 2, 1, 4, 5, 4]
    print("Input: ", sample)
    print("Deduped:", dedupe(sample))


if __name__ == "__main__":
    main()
