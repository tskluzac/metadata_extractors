import numpy as np
import pickle as pkl
from sklearn.metrics import accuracy_score, recall_score, precision_score
from sklearn.model_selection import ShuffleSplit
from math import isnan

np.set_printoptions(threshold=np.nan)


def is_number_or_none(field):
    """Determine if a string is a number or NaN by attempting to cast to it a float.

        :param field: (str) field
        :returns: (bool) whether field can be cast to a number"""

    if field is None:
        return True
    try:
        float(field)
        return True
    except ValueError:
        return False


def get_text_rows(matrix):
    """Get indices of all rows that have non-numerical aggregates.

        :param matrix: (np.array) matrix of data
        :returns: (list(int)) list of text indices to remove"""

    to_remove = []
    for i in range(0, len(matrix)):
        if not np.vectorize(is_number_or_none)(matrix[i]).all() \
                or np.vectorize(lambda x: str(x).lower() == "nan" or x is None)(matrix[i]).all():
            to_remove.append(i)

    return to_remove


def fill_zeros(matrix):
    """Fills all NaN and infinite entries with zeros.

        :param matrix: (np.array) matrix of data
        :returns: (np.array) matrix with zeros filled"""

    num_rows, num_cols = matrix.shape
    output_matrix = np.empty(matrix.shape)
    for i in range(0, num_rows):
        for j in range(0, num_cols):
            if matrix[i][j] is None or isnan(float(matrix[i][j])) or float(matrix[i][j]) == float('inf'):
                output_matrix[i][j] = np.float64(0)
            else:
                output_matrix[i][j] = matrix[i][j]

    return output_matrix


def clean_data(X, y=None):
    """Removes textual rows and fills zeros.

        :param X: (np.array) data matrix
        :param y: (np.array) true value column vector
        :returns: (np.array) cleaned matrix ready for model"""

    to_remove = get_text_rows(X)
    X = np.delete(X, to_remove, axis=0)
    X = fill_zeros(X)
    if y is not None:
        y = np.delete(y, to_remove, axis=0)
        return X, y
    else:
        return X


def cross_validation(model, X, y, splits=1000, decision_threshold=None):
    """Runs cross-validation on a test set to find accuracy of model and prints results.

        :param model: (sklearn.model) model to test
        :param X: (np.array) data matrix
        :param y: (np.array) true value column vector
        :param splits: (int) number of times to perform cross-validation
        :param decision_threshold: (float | None) if the model has a decision function
        such as distance to separating hyperplane, this will print statistics for
        only those observations within the threshold
        :returns: (list, np.array) null values and column vector with index of null in list"""

    all_y_test = np.zeros((0, 1))
    all_y_pred = np.zeros((0, 1))

    all_y_decision = np.zeros((0, 1))

    for train_inds, test_inds in ShuffleSplit(n_splits=splits, test_size=0.01).split(X, y):
        # Split off the train and test set
        X_test, y_test = X[test_inds, :], y[test_inds]
        X_train, y_train = X[train_inds, :], y[train_inds]

        # Train the model
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test).reshape(-1, 1)

        print y_pred
        raw_input()

        all_y_test = np.concatenate((all_y_test, y_test))
        all_y_pred = np.concatenate((all_y_pred, y_pred))

        if decision_threshold is not None:
            print "calculating decision function"
            print model.decision_function(X_test[0])
            y_decision = model.decision_function(X_test).reshape(-1, 1)
            all_y_decision = np.concatenate((all_y_decision, y_decision))
            print y_decision
            print "finished decision function"

    print "accuracy: {}\nprecision: {}\nrecall: {}".format(
        accuracy_score(all_y_test, all_y_pred),
        precision_score(all_y_test, all_y_pred, average='macro'),
        recall_score(all_y_test, all_y_pred, average='macro')
    )

    if decision_threshold is not None:
        print """"----------------------------
        Within decision threshold: {}
        ----------------------------""".format(decision_threshold)

        outside_threshold = [i for i in range(0, len(all_y_decision))
                             if abs(all_y_decision[i]) > decision_threshold]
        all_y_test = np.delete(all_y_test, outside_threshold)
        all_y_pred = np.delete(all_y_test, outside_threshold)

        print "accuracy: {}\nprecision: {}\nrecall: {}".format(
            accuracy_score(all_y_test, all_y_pred),
            precision_score(all_y_test, all_y_pred, average='macro'),
            recall_score(all_y_test, all_y_pred, average='macro')
        )


def train_and_save(model, X, y, file_name):
    """Train the model on the input data and save it for use in the pipeline.

        :param model: (sklearn.model) model to test
        :param X: (np.array) data matrix
        :param y: (np.array) true value column vector
        :param file_name: (string) file name of model"""

    model.fit(X, y)
    with open(file_name, "wb") as f:
        pkl.dump(model, f)
