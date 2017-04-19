import pytest
import numpy as np
from src.model.negotiation.preprocess import DialogueBatch, DataGenerator, Preprocessor, create_mappings, TextIntMap, Dialogue
from src.basic.schema import Schema
from src.basic.price_tracker import PriceTracker
from src.basic.util import read_json
from src.basic.scenario_db import ScenarioDB
from src.basic.dataset import read_examples
from itertools import izip

@pytest.fixture(scope='module')
def schema():
    schema_path = 'data/negotiation/craigslist-schema.json'
    return Schema(schema_path)

@pytest.fixture(scope='module')
def scenarios(schema):
    scenarios_path = 'data/negotiation/craigslist-scenarios.json'
    scenario_db = ScenarioDB.from_dict(schema, read_json(scenarios_path))
    return scenario_db

@pytest.fixture(scope='module')
def lexicon():
    return PriceTracker()

@pytest.fixture(scope='module')
def examples(schema):
    data_paths = ['data/negotiation/bot-chat-rulebased.json']
    return read_examples(None, data_paths, 10)

@pytest.fixture(scope='module')
def preprocessor(schema, lexicon):
    return Preprocessor(schema, lexicon, 'canonical', 'canonical', 'canonical')

@pytest.fixture(scope='module')
def generator(examples, lexicon, schema, preprocessor):
    return DataGenerator(examples, examples, None, preprocessor, schema)

class TestPreprocess(object):
    def test_process_example(self, preprocessor, examples, capsys):
        for dialogue in preprocessor._process_example(examples[0]):
            with capsys.disabled():
                print '\n========== Example dialogu (speaking agent=%d) ==========' % dialogue.agent
                print examples[0]
                for i, (agent, turn) in enumerate(izip(dialogue.agents, dialogue.token_turns[0])):
                    print 'agent=%d' % agent
                    for utterance in turn:
                        print utterance

    @pytest.fixture(scope='class')
    def processed_dialogues(self, preprocessor, examples):
        dialogues = [dialogue for dialogue in preprocessor._process_example(examples[0])]
        return dialogues

    @pytest.fixture(scope='class')
    def textint_map(self, processed_dialogues, schema, preprocessor):
        mappings = create_mappings(processed_dialogues, schema, preprocessor.entity_forms.values())
        textint_map = TextIntMap(mappings['vocab'], preprocessor)
        return textint_map

    def test_normalize_turn(self, generator, capsys):
        generator.convert_to_int()
        dialogues = generator.dialogues['train'][:2]
        batches = generator.create_dialogue_batches(dialogues, 1)
        assert len(batches) == 2

        with capsys.disabled():
            for i in xrange(2):  # Which perspective
                batch = batches[i]
                print '\n========== Example batch =========='
                for j in xrange(1):  # Which batch
                    print 'agent:', batch['agent'][j]
                    batch['kb'][j].dump()
                    for t, b in enumerate(batch['batch_seq']):
                        print t
                        print 'encode:', generator.textint_map.int_to_text(b['encoder_inputs'][j])
                        print 'encode last ind:', b['encoder_inputs_last_inds'][j]
                        print 'encoder tokens:', None if not b['encoder_tokens'] else b['encoder_tokens'][j]
                        print 'decode:', generator.textint_map.int_to_text(b['decoder_inputs'][j])
                        print 'decode last ind:', b['decoder_inputs_last_inds'][j]
                        print 'targets:', generator.textint_map.int_to_text(b['targets'][j])
                        print 'decoder tokens:', b['decoder_tokens'][j]
