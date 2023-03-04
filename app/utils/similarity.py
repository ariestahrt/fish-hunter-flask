import math
from sklearn.feature_extraction.text import CountVectorizer
import pandas, numpy
from ngram import NGram as NGramOri
# Contains text similarity measurements

# Levenshtein distance
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    # return similarity score and the distance
    return 1 - previous_row[-1] / len(s1), previous_row[-1]

# Jaro-Winkler distance
def jaro_winkler_distance(s1, s2):
    # Length of two strings
    len1 = len(s1)
    len2 = len(s2)
 
    # Maximum distance upto which matching
    # is allowed
    max_dist = int(max(len1, len2) / 2) - 1
 
    # Count of matches
    match = 0
 
    # Hash for matches
    hash_s1 = [0] * len1
    hash_s2 = [0] * len2
 
    # Traverse through the first string
    for i in range(len1):
 
        # Check if there is any matches
        for j in range(max(0, i - max_dist),
                       min(len2, i + max_dist + 1)):
 
            # If there is a match
            if (s1[i] == s2[j] and hash_s2[j] == 0):
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break
 
    # If there is no match
    if (match == 0):
        return 0
 
    # Number of transpositions
    t = 0
    point = 0
 
    # Count number of occurances
    # where two characters match but
    # there is a third matched character
    # in between the indices
    for i in range(len1):
        if (hash_s1[i]):
 
            # Find the next matched character
            # in second string
            while (hash_s2[point] == 0):
                point += 1
 
            if (s1[i] != s2[point]):
                t += 1
 
            point += 1
 
    # Return the Jaro-Winkler Similarity and the distance
    return ((match / len1) +
            (match / len2) +
            ((match - t / 2) / match)) / 3

# Calculate jacard by vector
def calculate_jaccard(arr1, arr2):
    intersection = len(list(set(arr1).intersection(arr2)))
    union = (len(arr1) + len(arr2)) - intersection
    return float(intersection) / union

# Calculate cosine from vector
def calculate_cosine(arr1, arr2):
    numerator = sum([arr1[i] * arr2[i] for i in range(0, len(arr1))])
    len_vec1 = math.sqrt(sum([x ** 2 for x in arr1]))
    len_vec2 = math.sqrt(sum([x ** 2 for x in arr2]))

    denominator = len_vec1 * len_vec2

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

# Bag of words
def clean_text(text):
    text = text.lower()
    chars = [',', '.', '!', '?', ';', ':', '(', ')', '[', ']', '{', '}', '/', '\\', '\'', '\"', '-', '_', '+', '=', '*', '&', '^', '%', '$', '#', '@', '~', '`', '>', '<', '|']
    for c in chars:
        text = text.replace(c, '')
    
    # Remove stop words
    stop_words = ['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with']
    for word in stop_words:
        text = text.replace(' ' + word + ' ', ' ')
    
    return text

# Cosine similarity
def cosine_similarity(s1, s2):
    count_vect = CountVectorizer()
    text_arr_tokenize = count_vect.fit_transform([s1, s2])

    return calculate_cosine(text_arr_tokenize.toarray()[0], text_arr_tokenize.toarray()[1])

# Create n-gram
def n_gram(s, n):
    n_gram = []
    # Filter
    filter = ['\n', '\t', ' ', '.']
    # clean text
    s_temp = s
    for f in filter:
        s_temp = s_temp.replace(f, '')

    # Create n-gram
    for i in range(0, len(s_temp) - n + 1):
        n_gram.append(s_temp[i:i+n])

    return n_gram

# Tokenize the n-gram result
# Return the vector of n-gram
def tokenize_n_gram(n_gram):
    n_gram_dict = {}
    for n in n_gram:
        if n in n_gram_dict:
            n_gram_dict[n] += 1
        else:
            n_gram_dict[n] = 1
    return n_gram_dict    

# Count Vectorizer
# Desc : Count the number of words in the sentence
def count_vectorizer(s1, s2):
    s1_n_gram = n_gram(s1, 1)
    s2_n_gram = n_gram(s2, 1)
    s1_n_gram_dict = tokenize_n_gram(s1_n_gram)
    s2_n_gram_dict = tokenize_n_gram(s2_n_gram)
    
    # generate vector based on s1 keys and s2 keys
    s1_keys = s1_n_gram_dict.keys()
    s2_keys = s2_n_gram_dict.keys()
    
    # combine the keys
    keys = set(s1_keys).union(set(s2_keys))

    # generate vector
    s1_vector = [s1_n_gram_dict.get(key, 0) for key in keys]
    s2_vector = [s2_n_gram_dict.get(key, 0) for key in keys]

    # print dataframe
    df = pandas.DataFrame([s1_vector, s2_vector], columns=numpy.array(list(keys)))
    # print(df)

    return s1_vector, s1_vector

def count_vectorizer2(s1, s2):
    count_vect = CountVectorizer()
    text_arr_tokenize = count_vect.fit_transform([s1, s2])

    # print dataframe
    # print(pandas.DataFrame(text_arr_tokenize.toarray(), columns=count_vect.get_feature_names_out()))

    return text_arr_tokenize.toarray()[0], text_arr_tokenize.toarray()[1]

def ngram_similarity(s1, s2, n):
    s1_n_gram = n_gram(s1, n)
    s2_n_gram = n_gram(s2, n)
    s1_n_gram_dict = tokenize_n_gram(s1_n_gram)
    s2_n_gram_dict = tokenize_n_gram(s2_n_gram)

    # print ngram set
    # print("s1", s1_n_gram)
    # print("s2", s2_n_gram)
    
    # combine the keys
    keys = set(s1_n_gram_dict.keys()).union(set(s2_n_gram_dict.keys()))

    # get same gram
    same_gram = 0
    total_gram = 0
    for key in keys:
        same_gram += min(s1_n_gram_dict.get(key, 0), s2_n_gram_dict.get(key, 0))
        total_gram += s1_n_gram_dict.get(key, 0) + s2_n_gram_dict.get(key, 0)
    
    # print same gram
    # print("same gram", same_gram)
    # print("total gram", total_gram)

    # dice coefficient
    return 2 * same_gram / total_gram

# Longest Common Subsequence
def lcs(setA, setB):
    dp = [[0 for i in range(len(setB)+1)] for j in range(len(setA)+1)]
    for i in range(1, len(setA)+1):
        for j in range(1, len(setB)+1):
            if setA[i-1] == setB[j-1]:
                dp[i][j] = 1 + dp[i-1][j-1]
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
    i=len(setA)
    j=len(setB)
    res=[]

    # Dapatkan subsequencenya
    while i > 0 and j > 0:
        if setA[i-1] == setB[j-1]:
            res=[setB[j-1]]+res
            j-=1
            i-=1
        else:
            if dp[i-1][j] > dp[i][j-1]:
                i-=1
            else:
                j-=1

    # Return berupa panjang subsequencenya dan subsequence itu sendiri
    return [dp[len(setA)][len(setB)] , res]

# LCS
def calculate_by_lcs(s1, s2):
    # vectorize using ngram
    s1_n_gram = n_gram(s1, 1)
    s2_n_gram = n_gram(s2, 1)

    lcs_res = lcs(s1_n_gram, s2_n_gram)
    
    # print("lcs_res", lcs_res)

    # dice coefficient
    return 2 * lcs_res[0] / (len(s1_n_gram) + len(s2_n_gram))

# Calculate Dict similarity
def calculate_dict_similarity(dict1, dict2):
    # combine the keys
    keys = set(dict1.keys()).union(set(dict2.keys()))
    
    # get match
    match = 0
    total = 0
    len_dict1 = 0
    len_dict2 = 0

    data_show = []

    for key in keys:
        vals1 = dict1.get(key, [])
        vals2 = dict2.get(key, [])
        data_append = [key, ",".join(vals1), ",".join(vals2)]
        data_show.append(data_append)
        len_dict1 += len(vals1)
        len_dict2 += len(vals2)

        # intersection
        sub_match = len(set(vals1).intersection(set(vals2)))
        # union
        sub_total = len(set(vals1).union(set(vals2)))
        # add to total
        match += sub_match
        total += sub_total

    # for ds in data_show:
    #     for d in ds:
    #         print(d, end=";")
    #     print()

    # calculate similarity
    by_default = match / total

    # print("match", match)
    # print("len(dict1)", len_dict1)
    # print("len(dict2)", len_dict2)

    by_dice = 2 * match / (len_dict1 + len_dict2)

    return by_default, by_dice

# Main
if __name__ == "__main__":
    s1 = "ariesta"
    s2 = "madesuta"
    print("Levenshtein distance: ", levenshtein_distance(s1, s2))
    print("Jaro-Winkler distance: ", jaro_winkler_distance(s1, s2))

    # vectorizer by ngram=1
    v1, v2 = count_vectorizer(s1, s2)
    by_jaccard = calculate_jaccard(v1, v2)
    print("Jacard similarity + 1gram: ", by_jaccard)

    # Calculate by cosine using ngram=1
    by_cosine = calculate_cosine(v1, v2)
    print("Cosine similarity + 1gram: ", by_cosine)

    # Calculate by ngram similarity
    by_ngram = NGramOri.compare(s1, s2, N=1)
    print("NGram similarity: ", by_ngram)

    # Calculate by cosine similarity
    by_cosine = cosine_similarity(s1, s2)
    print("Cosine similarity by word: ", by_cosine)
    