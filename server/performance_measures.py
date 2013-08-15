


import bpr

class PerformanceMeasure(object):

    def __init__(self, token_eval):

        self.token_eval = token_eval

        return


    def evaluate(self, prediction_file, goldstd_file):
        
        class BPROptions:
            pass
        bpr_options = BPROptions()
        bpr_options.goldFile = goldstd_file 
        bpr_options.predFile = prediction_file
        bpr_options.weightFile = None
        bpr_options.micro = False
        bpr_options.strictalts = False
        bpr_options.tokens = False
        if self.token_eval: 
           bpr_options.tokens = True
            
        pre, rec, f, pre_n, rec_n = bpr.run_evaluation(bpr_options)

        performance = {'target measure id' : None, 'target measure' : None, 'all' : []}

        performance['target measure id'] = 'F-measure'
        performance['target measure'] = f*100

        performance['all'].append(('precision', pre*100))
        performance['all'].append(('recall', rec*100))
        performance['all'].append(('F-measure', f*100))

        return performance

    



