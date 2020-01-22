odoo.define('js_website_images.basic_fields', function (require) {
	"use strict";

	var utils = require('web.utils');
	var session = require('web.session');
	var FieldBinaryImage = require('web.basic_fields').FieldBinaryImage;

	FieldBinaryImage.include({
		_render: function () {
			// Si la opción no_cache está a true y tiene un valor y es un "attachment"
			if (this.nodeOptions.no_cache && this.value && utils.is_bin_size(this.value)) {
				this.placeholder = session.url('/web/image', {
					model: this.model,
					id: JSON.stringify(this.res_id),
					field: this.nodeOptions.preview_image || this.name,
					// Generamos el número aleatorio
                    unique: Math.round(Math.random() * 100000000)
				});

                // Ponemos el valor a false para que al llamar al padre no se actualize de nuevo la URL
                this.value = false
			}

			// Llamamos al padre
            this._super();
		}
	})
});
