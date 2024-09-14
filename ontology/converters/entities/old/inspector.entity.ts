import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Inspector } from '@wsphere/inspections/domain';
import { Column, PrimaryColumn } from 'typeorm';
import { InspectorAggregate } from '../models';

@VsolvEntity({ prefix: 'inspct', name: 'inspector' }, ['tenant'])
export class InspectorEntity implements Inspector.Model {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true, unique: true })
  referenceId!: string | null;

  @Column({ nullable: true })
  name!: string | null;

  @Column({ nullable: true })
  email!: string | null;

  @Column({ nullable: true })
  phone!: string | null;

  toAggregate(publisher?: EventPublisher): InspectorAggregate {
    return mergeObjectContext(
      new InspectorAggregate({
        id: this.id,
        referenceId: this.referenceId,

        name: this.name,
        email: this.email,
        phone: this.phone,
      }),
      publisher
    );
  }
}
