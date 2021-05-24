import numpy as np
from absl import app, flags
import tensorflow as tf

from clip_tf.model import build_model
import converter

_MODELS = {
    "RN50": "https://openaipublic.azureedge.net/clip/models/afeb0e10f9e5a86da6080e35cf09123aca3b358a0c3e3b6c78a7b63bc04b6762/RN50.pt",
    "RN101": "https://openaipublic.azureedge.net/clip/models/8fa8567bab74a42d41c5915025a8e4538c3bdbe8804a470a72f30b0d94fab599/RN101.pt",
    "RN50x4": "https://openaipublic.azureedge.net/clip/models/7e526bd135e493cef0776de27d5f42653e6b4c8bf9e0f653bb11773263205fdd/RN50x4.pt",
    "ViT-B/32": "https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt",
}

FLAGS = flags.FLAGS
flags.DEFINE_enum('model', 'RN50', _MODELS.keys(), 'Which model to convert')
flags.DEFINE_string('output', 'CLIP_{model}', 'Filename of converted weights file. (format string)')

# model input for verification
image_url = "https://github.com/openai/CLIP/blob/main/CLIP.png?raw=true"
text_options = ["a diagram", "a dog", "a cat", "a neural network"]


def main(argv):
    model_url = _MODELS[FLAGS.model]
    state_dict = converter.download_statedict(model_url)
    model = build_model(state_dict)

    # predict to build shapes (model.build doesnt work, as it only supports float inputs)
    model.predict((
        np.ones((1, 224, 224, 3), np.float32),
        np.ones((1, 4, 77), np.int64)
    ))
    converter.load_pytorch_weights(model, state_dict, verbose=False)

    converter.verify(FLAGS.model, model, image_url, text_options, verbose=True)

    # create SavedModel
    output_filename = FLAGS.output.format(model=FLAGS.model.replace("/", "_"))
    model.save(output_filename)

    # load and test model
    model = tf.keras.models.load_model(output_filename)
    model.summary()
    converter.verify(FLAGS.model, model, image_url, text_options, verbose=True)


if __name__ == '__main__':
    app.run(main)
