import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Customer } from '@wsphere/customers/domain';
import { Column, PrimaryColumn } from 'typeorm';
import { CustomerAggregate } from '../models';

@VsolvEntity({ prefix: 'cus', name: 'customer' }, ['tenant'])
export const person_Person = new EntitySchema({
    "name": "Customer",
    "columns": {
        "id": {
            "type": "String",
            "primary": true,
            "generated": true
        },
        "Email": {
            "type": "String"
        },
        "Name": {
            "type": "String"
        },
        "Phone": {
            "type": "String"
        }
    },
    "relations": {}
})