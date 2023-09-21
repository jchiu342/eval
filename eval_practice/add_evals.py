from eval.models import Eval
import pickle

EVAL_PATH = "/mnt/c/Users/wtasf/OneDrive/Documents/go/projects/eval-practice/move_evals.pkl"
GO4GO_PATH = "/mnt/c/Users/wtasf/OneDrive/Documents/go/projects/go4go_db"
eval_pickle = pickle.load(open(EVAL_PATH, "rb"))

def add_to_db():
  for (name, info) in list(eval_pickle.items()):
    with open(GO4GO_PATH + "/" + name + ".sgf", "r") as sgf:
      content = sgf.read()
    info = list(info.items())[0]
    try:
      e = Eval(name=name, sgf_content=content, move=info[0], score=info[1]['scoreLead'])
      e.save()
    except Exception as f:
      print(f)
      break