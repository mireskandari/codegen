import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Customer } from '@wsphere/customers/domain';
import { Column, PrimaryColumn } from 'typeorm';
import { CustomerAggregate } from '../models';

@VsolvEntity({ prefix: 'cus', name: 'customer' }, ['tenant'])
export class CustomerEntity implements Customer.Model {
  @Column({ nullable: true, unique: true })
  referenceId!: string | null;

  toAggregate(publisher?: EventPublisher): CustomerAggregate {
    return mergeObjectContext(
      new CustomerAggregate({
        id: this.id,
        referenceId: this.referenceId,

        name: this.name,
        email: this.email,
        phone: this.phone,
      }),
      publisher
    );
  }


  // Below this line is ontology information 
  @PrimaryColumn()
  id!: string;

  @Column()
  name!: string;

  @Column()
  email!: string;

  @Column({ nullable: true })
  phone!: string | null;
}
