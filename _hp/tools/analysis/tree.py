import json
import subprocess
from pathlib import Path

import h2o
from h2o.tree import H2OTree, H2OSplitNode, H2OLeafNode
from h2o.estimators import H2ORandomForestEstimator

from chefboost import Chefboost as chef
import shutil

from anytree import AnyNode, RenderTree
from anytree.exporter import JsonExporter


import warnings
warnings.filterwarnings("ignore", "Dropping bad") # Ignore the warning that some columns are constant (they will just be ignored)
warnings.filterwarnings("ignore", "Sample rate") # Ignore that we do not have a test dataset (this is what we want)


h2o_jar = "helpers/h2o-3.44.0.2/h2o.jar"


config = {
    "ntrees": 10,
    "max_depth": 0, # Limit the depth of the tree (0: unlimited)
    "min_rows": 1,  # Minimum number of rows for a leaf node
    "stopping_rounds": 0,
    "stopping_metric": "auto",
    "seed": 0,
    "mtries": -2, 
    "sample_rate": 0.8,
    "nfolds": 10,
    "min_split_improvement": 0, # 0.01
    "binomial_double_trees": True,
    "score_each_iteration": True,
    "score_tree_interval": 0,
}

def replace_string(row):
    """Removes " in strings (h2o bug)."""                                          
    if type(row) == str:
        return row.replace('"', "")
    return row


def create_tree(hf, test_property, prediction_properties):
    """Create a decision tree for a given frame and test_property."""
    tree_model = H2ORandomForestEstimator(**config)
    tree_model.train(x=prediction_properties,
          y=test_property,
          training_frame=hf)

    return tree_model

def convert_tree(tree_model, tree_name, tree_id=0, base_dir=None):
    """Converts a tree to a mojo, dot and png and save everything."""
    mojo_path = f"{base_dir}/mojo/{tree_name}.mojo"
    dot_path = f"{base_dir}/dot/{tree_name}.gv"
    svg_path = f"{base_dir}/svg/{tree_name}.svg"
    if tree_model is not None:
        tree_model.download_mojo(mojo_path)
    result = subprocess.call(["java", "-cp", h2o_jar, "hex.genmodel.tools.PrintMojo", "--tree", str(tree_id), "-i", mojo_path, "-o", dot_path, "-f", "20", "-d", "3"])
    if result:
        print("Error occured!")
        return
    result = subprocess.Popen(["dot", "-Tsvg", dot_path, "-o", svg_path])
    return svg_path

def add_childs(parent, node):
    """Helper to create anytrees from h2o."""
    left_child = node.left_child
    left_split = node.left_levels
    if type(left_child) == H2OSplitNode:
        left = AnyNode(path=f"{parent.split}:{left_split}", split=left_child.split_feature, parent=parent)
        add_childs(left, left_child)
    else:
        AnyNode(path=f"{parent.split}:{left_split}", pred=left_child.prediction, parent=parent)
    right_child = node.right_child
    right_split = node.right_levels
    if type(right_child) == H2OSplitNode:
        right = AnyNode(path=f"{parent.split}:{right_split}", split=right_child.split_feature, parent=parent)
        add_childs(right, right_child)
    else:
        AnyNode(path=f"{parent.split}:{right_split}", pred=right_child.prediction, parent=parent)

def convert_anytree(tree_model, tree_name, df, base_dir):
    """Convert h2o tree to anytree."""
    vals = json.loads(df["outcome_str"].value_counts().to_frame().reset_index().rename(columns={"outcome_str": "outcome"}).to_json(orient="index"))
    path = f"{base_dir}/obs/{tree_name}.json"
    with open(path, "w") as f:
        json.dump(vals, f)
    for num, val in vals.items():
        try:
            ob = val["outcome"]
            tree = H2OTree(model = tree_model, tree_number = 0 , tree_class = ob)
            root_t = tree.root_node
            if type(root_t) == H2OLeafNode:
                root = AnyNode(path="root:root", pred=root_t.prediction)
            else:
                root = AnyNode(path="root:root", split=tree.root_node.split_feature)
                add_childs(root, root_t)
            path = f"{base_dir}/anytree/{tree_name}_{num}.json"
            with open(path, "w") as f:
                JsonExporter().write(root, f)
        except h2o.exceptions.H2OResponseError:
            pass

def create_tree_dirs(base_dir):
    """Create the dirs for the decision trees if not existing already."""
    Path(f"{base_dir}/mojo/").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/dot/").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/svg/").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/anytree/").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/obs/").mkdir(parents=True, exist_ok=True)
    Path(f"{base_dir}/py/").mkdir(parents=True, exist_ok=True)


    with open(f"{base_dir}/config.json", "w") as f:
        json.dump(config, f)


def create_trees_chefboost(data, name, base_dir):
    data["raw_header"] = data["raw_header"].apply(lambda x: x.replace("'", ""))
    data["outcome_str"] = data["outcome_str"].apply(lambda x: x.replace("'", ""))
    for algo in ["ID3", "C4.5", "CART", "CHAID"]:
        config = {'algorithm': algo, 'enableParallelism': True} # ID3, C4.5, CART, CHAID
        model = chef.fit(data, config = config, target_label = 'outcome_str')
        shutil.move("outputs/rules/rules.py", f"{base_dir}/py/{name}_{algo}.py")

def make_tree(df, prediction_properties, test_name, base_dir):
    h2o.connect()
    create_tree_dirs(base_dir)
    tree_name = f"{test_name}"
    if len(df) < 20:
        config["nfolds"] = 0
    else:
        config["nfolds"] = 10
    print(f"Create tree: {tree_name}, datapoints: {len(df)}")
    num_columns = len(df.columns)
    
    df = df.astype(str)

    # Quite slow and not very helpful?
    # create_trees_chefboost(df, test_name, base_dir)

    df = df.astype("category")
    df["outcome_str"] = df["outcome_str"].apply(replace_string)
    df["outcome_str"] = df["outcome_str"].cat.remove_unused_categories()
    hf = h2o.H2OFrame(df, column_types=["enum" for _ in range(num_columns)])

    tree_model = create_tree(hf, "outcome_str", prediction_properties)
    img_path = convert_tree(tree_model, tree_name, tree_id=0, base_dir=base_dir)
    convert_anytree(tree_model, tree_name, df, base_dir)
    
    return tree_model

