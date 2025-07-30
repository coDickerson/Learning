import pandas as pd
from sklearn.cluster import KMeans 
from sklearn.metrics.pairwise import cosine_similarity
from classificationcluster import classify

# recommend other correlated companies to meet based on previous behavior
# ie: 80% of the clients who requested meetings with Block also requested meetings with Dataiku…
#     do you want to go ask your client if they might be interested?

def recommend(df, source_company_id, source_company_map,  threshold=.4):
    # binary interaction matrix
    # describes if a target company was requested by a source, 1=yes and 0=no
    interaction_matrix = pd.crosstab(df['source_company'], df['target_company'])

    # pearson correlation
    company_corr = interaction_matrix.corr(method='pearson')

    # checks if company id exists
    if source_company_id not in interaction_matrix.index:
        print(f'Investor {source_company_id} not found.')
        return

    # source company row from map and list of requested companies
    source_company_row = source_company_map[source_company_id]
    requested_companies = source_company_row.requested

    pairwise_recs = pairwise(interaction_matrix, company_corr, requested_companies, threshold)
    # multivector_recs = multivector(interaction_matrix, source_company_id, requested_companies)
    visualization(interaction_matrix, pairwise_recs)
    
def pairwise(company_corr, requested_companies, threshold):
    # flattens correlation matrix into a workable table
    # filters out correlation below threshold and finds pairs with one company from requsted companies list
    company_corr.columns.name = None
    company_corr.index.name = None
    company_pairs = company_corr.stack().reset_index() # flattens square matrix
    company_pairs.columns = ['company_a', 'company_b', 'correlation']
    company_pairs = company_pairs[company_pairs['company_a'] < company_pairs['company_b']] # deals with duplicates and same company correlations
    significant_pairs = company_pairs[company_pairs['correlation'] > threshold] 
    filtered = significant_pairs [
    ((significant_pairs['company_a'].isin(requested_companies)) & (~significant_pairs['company_b'].isin(requested_companies))) | 
    ((significant_pairs['company_b'].isin(requested_companies)) & (~significant_pairs['company_a'].isin(requested_companies)))
    ]
    filtered = filtered.sort_values(by='correlation', ascending=False)
    # adds other company and correlation to suggestions list
    suggestions = []
    for _, row in filtered.iterrows():
        if row['company_a'] in requested_companies and row['company_b'] not in requested_companies:
            suggestions.append((row['company_b'], row['correlation']))
        elif row['company_b'] in requested_companies and row['company_a'] not in requested_companies:
            suggestions.append((row['company_a'], row['correlation']))
    # adds suggestions to data frame to be printed
    recommendations_df = pd.DataFrame(suggestions, columns=['recommended company', 'correlation'])
    recommendations_df = recommendations_df.drop_duplicates(subset='recommended company')
    recommendations_df = recommendations_df.sort_values(by='correlation', ascending=False)
    return recommendations_df

    
def multivector(interaction_matrix, source_company_id, requested_companies, top_n = 10):
    profile_vector = interaction_matrix.loc[source_company_id]
    company_vectors = interaction_matrix.T
    similarity_scores = cosine_similarity(company_vectors, profile_vector.values.reshape(1, -1)).flatten()
    # Assemble recommendation table
    similarity_df = pd.DataFrame({
        'company': company_vectors.index,
        'similarity': similarity_scores
    })
    # Remove already requested companies
    similarity_df = similarity_df[~similarity_df['company'].isin(requested_companies)]
    # Top recommendations
    recommendations_df = similarity_df.sort_values(by='similarity', ascending=False).head(top_n)
    print("\nHere are your top recommendations based on your full request profile:\n")
    print(recommendations_df)
    return recommendations_df


def visualization(interaction_matrix, recommendations_df):   
    print("\nHere are a list of similar companies that are based on your previous company requests:\n")
    print(recommendations_df.head(10))
    while(True) :
        user_input = input('Would you like a visualization (y/n):\n').strip().lower()
        if user_input == 'y':
            classify(recommendations_df, interaction_matrix)
            break
        elif user_input == 'n':
            print("Visualization skipped.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
    return (recommendations_df)