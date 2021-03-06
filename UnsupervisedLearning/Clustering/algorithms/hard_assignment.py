import sys
import time
from sklearn.metrics import pairwise_distances
import numpy as np
import matplotlib.pyplot as plt


class KMeans:
    """
    K means clustering algorithm.
    """
    # Implement k-means
    def get_initial_centroids(self, data, k, seed=None):
        """
        Randomly choose k data points as initial centroids
        """
        if seed is not None:  # useful for obtaining consistent results
            np.random.seed(seed)
        n = data.shape[0]  # number of data points

        # Pick K indices from range [0, N).
        rand_indices = np.random.randint(0, n, k)

        # Keep centroids as dense format, as many entries will be nonzero due to averaging.
        # As long as at least one document in a cluster contains a word,
        # it will carry a nonzero weight in the TF-IDF vector of the centroid.
        centroids = data[rand_indices, :].toarray()

        return centroids

    def smart_initialize(self, data, k, seed=None):
        """
        Use k-means++ to initialize a good set of centroids
        """
        if seed is not None:  # useful for obtaining consistent results
            np.random.seed(seed)
        centroids = np.zeros((k, data.shape[1]))

        # Randomly choose the first centroid.
        # Since we have no prior knowledge, choose uniformly at random
        idx = np.random.randint(data.shape[0])
        centroids[0] = data[idx, :].toarray()
        # Compute distances from the first centroid chosen to all the other data points
        squared_distances = pairwise_distances(data, centroids[0:1], metric='euclidean').flatten() ** 2

        for i in range(1, k):
            # Choose the next centroid randomly, so that the probability for each data point to be chosen
            # is directly proportional to its squared distance from the nearest centroid.
            # Roughtly speaking, a new centroid should be as far as from ohter centroids as possible.
            idx = np.random.choice(data.shape[0], 1, p=squared_distances / sum(squared_distances))
            centroids[i] = data[idx, :].toarray()
            # Now compute distances from the centroids to all data points
            squared_distances = np.min(pairwise_distances(data, centroids[0:i + 1], metric='euclidean') ** 2, axis=1)

        return centroids

    def assign_clusters(self, data, centroids):
        """

        :param data:
        :param centroids:
        :return:
        """
        distances = pairwise_distances(data, centroids, metric='euclidean')
        cluster_assignment = np.argmin(distances, axis=1)

        return cluster_assignment

    def revise_centroids(self, data, k, cluster_assignment):
        """

        :param data:
        :param k:
        :param cluster_assignment:
        :return:
        """
        new_centroids = []
        for i in range(k):
            # Select all data points that belong to cluster i. Fill in the blank (RHS only)
            member_data_points = data[cluster_assignment==i]
            # Compute the mean of the data points. Fill in the blank (RHS only)
            centroid = np.mean(member_data_points, axis=0)

            # Convert numpy.matrix type to numpy.ndarray type
            centroid = centroid.A1
            new_centroids.append(centroid)
        new_centroids = np.array(new_centroids)

        return new_centroids

    def compute_heterogeneity(self, data, k, centroids, cluster_assignment):
        """

        :param data:
        :param k:
        :param centroids:
        :param cluster_assignment:
        :return:
        """
        heterogeneity = 0.0
        for i in range(k):

            # Select all data points that belong to cluster i. Fill in the blank (RHS only)
            member_data_points = data[cluster_assignment == i, :]

            if member_data_points.shape[0] > 0:  # check if i-th cluster is non-empty
                # Compute distances from centroid to data points (RHS only)
                distances = pairwise_distances(member_data_points, [centroids[i]], metric='euclidean')
                squared_distances = distances ** 2
                heterogeneity += np.sum(squared_distances)

        return heterogeneity

    # Fill in the blanks
    def run_kmeans(self, data, k, initial_centroids, maxiter, record_heterogeneity=None, verbose=False):
        """
        This function runs k-means on given data and initial set of centroids.
           maxiter: maximum number of iterations to run.
           record_heterogeneity: (optional) a list, to store the history of heterogeneity as function of iterations
                                 if None, do not store the history.
           verbose: if True, print how many data points changed their cluster labels in each iteration
        """
        centroids = initial_centroids[:]
        prev_cluster_assignment = None
        cluster_assignment = None

        for itr in range(maxiter):
            if verbose:
                print(itr)

            # 1. Make cluster assignments using nearest centroids
            # YOUR CODE HERE
            cluster_assignment = self.assign_clusters(data, centroids)

            # 2. Compute a new centroid for each of the k clusters, averaging all data points assigned to that cluster.
            # YOUR CODE HERE
            centroids = self.revise_centroids(data, k, cluster_assignment)

            # Check for convergence: if none of the assignments changed, stop
            if prev_cluster_assignment is not None and \
                    (prev_cluster_assignment == cluster_assignment).all():
                break

            # Print number of new assignments
            if prev_cluster_assignment is not None:
                num_changed = np.sum(prev_cluster_assignment != cluster_assignment)
                if verbose:
                    print('    {0:5d} elements changed their cluster assignment.'.format(num_changed))

            # Record heterogeneity convergence metric
            if record_heterogeneity is not None:
                # YOUR CODE HERE
                score = self.compute_heterogeneity(data, k, centroids, cluster_assignment)
                record_heterogeneity.append(score)

            prev_cluster_assignment = cluster_assignment[:]

        return centroids, cluster_assignment

    def kmeans_multiple_runs(self, data, k, maxiter, num_runs, seed_list=None,
                             verbose=False):
        """

        :param data:
        :param k:
        :param maxiter:
        :param num_runs:
        :param seed_list:
        :param verbose:
        :return:
        """
        heterogeneity = {}

        min_heterogeneity_achieved = float('inf')
        best_seed = None
        final_centroids = None
        final_cluster_assignment = None

        for i in range(num_runs):

            # Use UTC time if no seeds are provided
            if seed_list is not None:
                seed = seed_list[i]
                np.random.seed(seed)
            else:
                seed = int(time.time())
                np.random.seed(seed)

            # Use k-means++ initialization
            initial_centroids = self.get_initial_centroids(data, k, seed=seed)

            # Run k-means
            centroids, cluster_assignment = self.run_kmeans(data, k, initial_centroids, maxiter,
                                                            record_heterogeneity=None, verbose=False)

            # To save time, compute heterogeneity only once in the end
            heterogeneity[seed] = self.compute_heterogeneity(data, k, centroids, cluster_assignment)

            if verbose:
                print('seed={0:06d}, heterogeneity={1:.5f}'.format(seed, heterogeneity[seed]))
                sys.stdout.flush()

            # if current measurement of heterogeneity is lower than previously seen,
            # update the minimum record of heterogeneity.
            if heterogeneity[seed] < min_heterogeneity_achieved:
                min_heterogeneity_achieved = heterogeneity[seed]
                best_seed = seed
                final_centroids = centroids
                final_cluster_assignment = cluster_assignment

        return final_centroids, final_cluster_assignment

    def plot_heterogeneity(self, heterogeneity, k):
        """

        :param heterogeneity:
        :param k:
        :return:
        """
        plt.figure(figsize=(7, 4))
        plt.plot(heterogeneity, linewidth=4)
        plt.xlabel('# Iterations')
        plt.ylabel('Heterogeneity')
        plt.title('Heterogeneity of clustering over time, K={0:d}'.format(k))
        plt.rcParams.update({'font.size': 16})
        plt.tight_layout()
        plt.show()


